"""
Sub-Agent B: Safety Gate Agent

Authors: Syed Ali Turab, Fergie Feng & Diana Liu | Team: Broadview
Date:   March 1, 2026

Detects emergency red flags in collected symptom data and triggers
immediate escalation messaging for life-threatening conditions.

This is the MOST SAFETY-CRITICAL agent in the pipeline. It runs
immediately after intake and BEFORE any triage or routing. If a red
flag is detected, the entire booking flow is stopped and the owner
is directed to an emergency clinic.

Design principle: CONSERVATIVE matching. When in doubt, flag it.
Under-triage (missing a real emergency) is far more dangerous than
over-triage (flagging a non-emergency).

Red flags are sourced from:
  - ASPCA Animal Poison Control (AnTox) — 1M+ documented cases
  - Veterinary emergency medicine guidelines
  - Common life-threatening conditions by species

The red flag list can be loaded from backend/data/red_flags.json
or falls back to the hardcoded DEFAULT_RED_FLAGS list.

Input:  Structured intake data (chief_complaint + symptom_details)
Output: red_flag_detected boolean + matched flags + escalation message
"""

import json
import os
import re
import logging

logger = logging.getLogger('petcare.agents.safety_gate')

# ---------------------------------------------------------------------------
# Temporal past-incident markers
# ---------------------------------------------------------------------------
# If any of these words appear within a short window around a red-flag match,
# the match is treated as a past/resolved incident rather than a current emergency.
# This prevents false positives like "he ate chocolate last year" or
# "she had a seizure before, but now she just has a limp".

_PAST_MARKERS = [
    # English
    'last year', 'last month', 'last week', 'last time', 'last night',
    'a year ago', 'months ago', 'weeks ago', 'days ago', 'ago',
    'previously', 'before', 'history of', 'used to', 'used to have',
    'had a', 'had an', 'happened before', 'in the past', 'resolved',
    'recovered', 'was treated', 'was seen', 'already seen',
    # French
    "l'année dernière", "l'an dernier", 'le mois dernier', 'la semaine dernière',
    'auparavant', 'avant', 'déjà', 'passé', 's\'est rétabli', 'a été traité',
    'il y a', 'par le passé', 'anciennement',
    # Spanish
    'el año pasado', 'el mes pasado', 'la semana pasada',
    'hace un año', 'hace meses', 'hace semanas', 'hace días',
    'antes', 'anteriormente', 'se recuperó', 'fue tratado', 'resuelto', 'ya',
    # Chinese (Simplified)
    '去年', '上个月', '上周', '以前', '之前', '曾经', '已经恢复', '已经治疗', '以往',
    # Arabic
    'العام الماضي', 'الشهر الماضي', 'الأسبوع الماضي', 'سابقاً', 'قبل',
    'تعافى', 'عولج', 'في الماضي',
    # Hindi
    'पिछले साल', 'पिछले महीने', 'पिछले हफ्ते', 'पहले', 'ठीक हो गया', 'इलाज किया गया',
    # Urdu
    'گزشتہ سال', 'گزشتہ ماہ', 'گزشتہ ہفتہ', 'پہلے', 'ٹھیک ہو گیا', 'علاج کیا گیا',
]
_PAST_WINDOW = 80  # characters either side of a flag match to scan for temporal markers


def _is_past_incident(text: str, flag: str) -> bool:
    """Return True if the flag match appears to be a past / resolved incident."""
    start = 0
    while True:
        idx = text.find(flag.lower(), start)
        if idx == -1:
            break
        window_start = max(0, idx - _PAST_WINDOW)
        window_end   = min(len(text), idx + len(flag) + _PAST_WINDOW)
        window = text[window_start:window_end]
        for marker in _PAST_MARKERS:
            if marker in window:
                return True
        start = idx + 1
    return False

# ---------------------------------------------------------------------------
# Default Red Flag List
# ---------------------------------------------------------------------------
# These are life-threatening conditions that require IMMEDIATE veterinary care.
# The list is intentionally broad — false positives are acceptable,
# false negatives are not.
#
# Sources: ASPCA AnTox database, veterinary emergency textbooks,
# common toxin ingestion scenarios.

DEFAULT_RED_FLAGS = [
    # Respiratory emergencies
    'difficulty breathing',
    'not breathing',
    'labored breathing',
    'gasping',
    'blue gums',
    'pale gums',

    # Hemorrhagic emergencies
    'uncontrolled bleeding',
    'heavy bleeding',
    'won\'t stop bleeding',

    # Neurological emergencies
    'seizure',
    'seizures',
    'convulsions',
    'tremors',

    # Collapse / unresponsive
    'collapse',
    'collapsed',
    'unresponsive',
    'unconscious',

    # Toxin ingestion (top toxins per ASPCA 2024 report)
    'toxin ingestion',
    'poison',
    'poisoning',
    'antifreeze',
    'chocolate toxicity',
    'rat poison',
    'ate medication',
    'ate xylitol',

    # Urinary obstruction (especially critical in male cats)
    'inability to urinate',
    'cannot urinate',
    'straining to urinate with no output',

    # Gastric emergencies
    'bloat',
    'distended abdomen',
    'gastric dilation',
    'trying to vomit but nothing coming up',

    # Trauma
    'hit by car',
    'trauma',
    'fall from height',

    # Ocular emergencies
    'eye injury',
    'eye popping out',
    'proptosis',

    # Environmental emergencies
    'severe burn',
    'drowning',
    'heat stroke',
    'hypothermia',
    'snake bite'
]

# ---------------------------------------------------------------------------
# Emergency Escalation Message
# ---------------------------------------------------------------------------
# This message is shown to the owner when any red flag is detected.
# It is intentionally direct and urgent — the goal is to get the pet
# to an emergency clinic as fast as possible.

ESCALATION_MESSAGE = (
    "⚠️ EMERGENCY DETECTED: Based on the symptoms you've described, this may be "
    "a life-threatening emergency. Please take your pet to the nearest emergency "
    "veterinary clinic IMMEDIATELY. Do not wait for a regular appointment.\n\n"
    "If you're unsure where the nearest emergency clinic is, call your regular "
    "vet's office — their voicemail often has emergency clinic information."
)


class SafetyGateAgent:
    """
    Rule-based emergency red-flag detection agent.

    Uses substring matching against a curated list of emergency terms
    to detect life-threatening conditions in the intake data.

    The matching is deliberately simple (substring search) rather than
    ML-based, because:
      1. False negatives are unacceptable for safety-critical detection
      2. Rule-based matching is deterministic and auditable
      3. The red-flag list can be updated without retraining
      4. It runs in <1ms (no API latency)

    For edge cases (e.g., "breathing funny" vs "can't breathe"), the
    LLM-powered Triage Agent (D) provides the nuanced assessment.
    The Safety Gate is the coarse-grained first filter.
    """

    def __init__(self, red_flags_path: str = None):
        """
        Initialize the Safety Gate with a red-flag list.

        Args:
            red_flags_path: Optional path to a JSON file containing
                            the red flag list. If not provided or file
                            doesn't exist, uses DEFAULT_RED_FLAGS.
        """
        self.agent_name = 'safety_gate'
        self.red_flags = self._load_red_flags(red_flags_path)

    def _load_red_flags(self, path: str = None) -> list:
        """
        Load red flags from a JSON file or fall back to defaults.

        The JSON file should have the format:
          { "red_flags": ["difficulty breathing", "seizure", ...] }

        Args:
            path: File path to red_flags.json.

        Returns:
            List of red flag strings (lowercased for matching).
        """
        if path and os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get('red_flags', DEFAULT_RED_FLAGS)
        return DEFAULT_RED_FLAGS

    def process(self, intake_data: dict) -> dict:
        """
        Check intake data for emergency red flags.

        Performs case-insensitive substring matching of each red flag
        term against the combined chief_complaint and symptom_details text.
        Any match triggers an escalation.

        Args:
            intake_data: Dict from the Intake Agent containing at minimum:
                - chief_complaint (str): Owner's description of symptoms
                - symptom_details (dict): Structured symptom information

        Returns:
            dict with standard agent output contract:
              - agent_name (str): 'safety_gate'
              - status (str): 'escalate' if red flag found, else 'success'
              - output (dict): red_flag_detected, red_flags list,
                escalation_message (or None)
              - confidence (float): 1.0 if flag found (certain),
                0.95 if no flag (high but not absolute — owner may
                not have described symptoms clearly)
              - warnings (list): Empty for this agent
        """
        # Combine all text sources for comprehensive matching.
        # We check both the free-text complaint and any structured fields.
        chief_complaint = intake_data.get('chief_complaint', '').lower()
        symptom_text = json.dumps(
            intake_data.get('symptom_details', {})
        ).lower()
        combined_text = f"{chief_complaint} {symptom_text}"

        # Check each red flag term against the combined text.
        # Skip matches that appear to be past/resolved incidents (temporal filter).
        detected_flags = []
        for flag in self.red_flags:
            if flag.lower() in combined_text:
                if _is_past_incident(combined_text, flag):
                    logger.debug(f"Red flag '{flag}' skipped — appears to be past incident")
                else:
                    detected_flags.append(flag)

        red_flag_detected = len(detected_flags) > 0

        if red_flag_detected:
            logger.warning(f"Red flags detected: {detected_flags}")

        return {
            'agent_name': self.agent_name,
            'status': 'escalate' if red_flag_detected else 'success',
            'output': {
                'red_flag_detected': red_flag_detected,
                'red_flags': detected_flags,
                'escalation_message': (
                    ESCALATION_MESSAGE if red_flag_detected else None
                )
            },
            # High confidence when a flag IS found (deterministic match).
            # Slightly lower when no flag found (owner might not describe
            # symptoms in terms we match).
            'confidence': 1.0 if red_flag_detected else 0.95,
            'warnings': []
        }
