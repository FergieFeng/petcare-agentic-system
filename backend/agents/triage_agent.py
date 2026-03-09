"""
Sub-Agent D: Triage Agent

Authors: Syed Ali Turab, Fergie Feng & Diana Liu | Team: Broadview
Date:   March 1, 2026
Code updated: Syed Ali Turab, March 4, 2026 — LLM triage with rule-based fallback.

Classifies urgency into four tiers based on validated symptom data,
with evidence-based rationale and confidence scoring.

Urgency Tiers:
  - Emergency:  Life-threatening, needs immediate care (go to ER NOW)
  - Same-day:   Significant concern, should be seen today
  - Soon:       Non-urgent but needs attention within 1-3 days
  - Routine:    Standard wellness or minor concern, schedule at convenience

The triage decision considers:
  - Symptom severity and type
  - Timeline (how long symptoms have persisted)
  - Eating/drinking status (reduced = more urgent)
  - Energy level (lethargic = more urgent)
  - Species-specific norms (e.g., cats hide symptoms → often more urgent
    by the time owners notice)
  - Number and combination of symptoms

Conservative by design: when borderline, the agent assigns the
HIGHER urgency tier. Under-triage is more dangerous than over-triage.

Input:  Validated intake data + safety gate result
Output: Urgency tier + rationale + confidence + contributing factors
"""

import logging
import os
import json
import openai
from langsmith.wrappers import wrap_openai
from backend.utils.llm_utils import llm_call_with_retry
from backend.utils.rag_retriever import retrieve_illness_context, format_rag_context

# os/json/openai for LLM triage; fallback to _rule_based_triage on error. (Syed Ali Turab, Mar 4, 2026)
logger = logging.getLogger('petcare.agents.triage')

# ---------------------------------------------------------------------------
# Urgency Tier Definitions
# ---------------------------------------------------------------------------

URGENCY_TIERS = ['Emergency', 'Same-day', 'Soon', 'Routine']

# Symptom severity signals that push urgency higher.
# These are checked against the intake data to inform the LLM's
# triage classification or rule-based fallback.
HIGH_URGENCY_SIGNALS = [
    'blood', 'bleeding', 'not eating', 'won\'t eat',
    'lethargic', 'lethargy', 'painful', 'crying',
    'swelling', 'rapid breathing', 'panting excessively',
    'not drinking', 'straining', 'foreign object',
    'ingested', 'ate something'
]

LOW_URGENCY_SIGNALS = [
    'mild', 'minor', 'small', 'slight',
    'eating normally', 'acting normal', 'playful',
    'one time', 'once'
]


class TriageAgent:
    """
    Urgency classification agent.

    Assigns one of four urgency tiers to each intake case based on
    the validated symptom data. Provides an evidence-based rationale
    and a confidence score.

    The primary path uses an LLM (gpt-4o-mini) with structured output.
    A rule-based signal-counting heuristic is kept as a fallback if the
    LLM call fails.

    Conservative default: when uncertain, assigns higher urgency.
    This is a deliberate design choice — it's safer to over-triage
    than to under-triage a potentially serious condition.
    """

    def __init__(self):
        """Initialize the Triage Agent."""
        self.agent_name = 'triage'

    def process(self, intake_data: dict, safety_result: dict, pet_profile: dict = None) -> dict:
        # LLM triage: classify urgency from species, complaint, timeline, eating, energy, breed, age, weight. (Syed Ali Turab, Mar 4, 2026)
        client = wrap_openai(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
        profile = pet_profile or intake_data.get('pet_profile', {})
        species = (intake_data.get('species') or profile.get('species', 'unknown'))
        breed  = profile.get('breed', '')
        age    = profile.get('age', '')
        weight = profile.get('weight', '')
        complaint = intake_data.get('chief_complaint', '')
        timeline = (intake_data.get('timeline', '') or
                    intake_data.get('symptom_details', {}).get('timeline', ''))
        eating = (intake_data.get('eating_drinking', '') or
                  intake_data.get('symptom_details', {}).get('eating_drinking', ''))
        energy = (intake_data.get('energy_level', '') or
                  intake_data.get('symptom_details', {}).get('energy_level', ''))

        # RAG: retrieve relevant illness KB entries to ground the LLM decision
        rag_entries = retrieve_illness_context(complaint, species=species, top_k=3)
        rag_block = format_rag_context(rag_entries, species=species)

        system_prompt = f"""You are a veterinary triage classification assistant. Your ONLY job is to classify urgency.

HARD RULES — never violate:
1. NEVER name a disease, condition, or diagnosis in any field (no pancreatitis, parvovirus, cancer, infection, etc.)
2. NEVER suggest medications or treatments
3. The rationale field is read ONLY by clinic staff — use clinical observation language but NO diagnosis names
4. Describe observations only: e.g. "vomiting x2 days + not eating = warrants same-day evaluation" — NOT "likely gastroenteritis"
5. Be conservative but accurate — lethargy or not eating alone without other acute signs is Same-day or Soon, NOT Emergency. Reserve Emergency only for immediate life-threatening presentations: collapse, inability to breathe, active seizure, known toxin ingestion, severe trauma, or uncontrolled bleeding.
6. Age context: geriatric (>8 yrs dog, >10 yrs cat) or very young (<6 months) animals warrant one tier higher when borderline.
7. Respond ONLY with valid JSON — no markdown, no preamble

Urgency tiers (use exactly these strings):
- Emergency: life-threatening, go to ER now
- Same-day: significant concern, must be seen today
- Soon: non-urgent, seen within 1-3 days
- Routine: standard wellness or minor concern

Respond with exactly:
{{
  "urgency_tier": "Emergency|Same-day|Soon|Routine",
  "rationale": "brief clinical observation for clinic staff only — no diagnosis names",
  "confidence": 0.0-1.0,
  "contributing_factors": ["observable factor 1", "observable factor 2"]
}}

{rag_block}"""

        profile_parts = [f"Species: {species}"]
        if breed:  profile_parts.append(f"Breed: {breed}")
        if age:    profile_parts.append(f"Age: {age}")
        if weight: profile_parts.append(f"Weight: {weight}")
        user_msg = ('\n'.join(profile_parts) +
                    f"\nChief complaint: {complaint}\n"
                    f"Timeline: {timeline}\nEating/drinking: {eating}\nEnergy level: {energy}")

        try:
            # Single LLM call with retry; parse JSON and validate tier.
            raw = llm_call_with_retry(
                client,
                model='gpt-4o-mini',
                max_tokens=300,
                temperature=0.1,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_msg}
                ]
            ).replace('```json', '').replace('```', '').strip()
            parsed = json.loads(raw)
            tier = parsed.get('urgency_tier', 'Soon')
            if tier not in ['Emergency', 'Same-day', 'Soon', 'Routine']:
                tier = 'Soon'
            conf = float(parsed.get('confidence', 0.8))
            return {
                'agent_name': self.agent_name,
                'status': 'success',
                'output': {
                    'urgency_tier': tier,
                    'rationale': parsed.get('rationale', ''),
                    'confidence': conf,
                    'contributing_factors': parsed.get('contributing_factors', [])
                },
                'confidence': conf,
                'warnings': []
            }
        except Exception as e:
            logger.error(f'Triage LLM error, falling back to rules: {e}')
            fallback = self._rule_based_triage(intake_data)
            fallback.setdefault('warnings', []).append(f'Fell back to rule-based triage: {str(e)}')
            return fallback

    # Rule-based fallback when LLM fails. Uses signal counts from intake text. (Syed Ali Turab, Mar 4, 2026)
    def _rule_based_triage(self, intake_data: dict) -> dict:
        """
        Classify urgency tier based on intake data and safety check.

        Rule-based fallback when the LLM triage call fails:
          - Count high-urgency signals in the complaint text
          - Count low-urgency signals
          - Adjust based on eating/drinking and energy levels
          - Apply species-specific modifiers (cats get +1 urgency bump)
          - Map the final score to a tier

        Args:
            intake_data: Dict from the Intake Agent with chief_complaint,
                         symptom_details, timeline, eating_drinking,
                         energy_level.

        Returns:
            dict with standard agent output contract:
              - agent_name (str): 'triage'
              - status (str): 'success'
              - output (dict): urgency_tier, rationale, confidence,
                contributing_factors
              - confidence (float): 0.0 to 1.0
              - warnings (list): Any issues
        """
        # ----- Rule-based fallback heuristic -----

        combined_text = (
            intake_data.get('chief_complaint', '') + ' ' +
            str(intake_data.get('symptom_details', ''))
        ).lower()

        # Count urgency signals
        high_count = sum(
            1 for signal in HIGH_URGENCY_SIGNALS
            if signal in combined_text
        )
        low_count = sum(
            1 for signal in LOW_URGENCY_SIGNALS
            if signal in combined_text
        )

        contributing_factors = []

        # Adjust for eating/drinking status
        eating = intake_data.get('eating_drinking', '').lower()
        if 'none' in eating or 'not eating' in eating:
            high_count += 2
            contributing_factors.append('Not eating/drinking')
        elif 'reduced' in eating:
            high_count += 1
            contributing_factors.append('Reduced eating/drinking')

        # Adjust for energy level
        energy = intake_data.get('energy_level', '').lower()
        if 'lethargic' in energy:
            high_count += 2
            contributing_factors.append('Lethargic')
        elif 'reduced' in energy:
            high_count += 1
            contributing_factors.append('Reduced energy')

        # Species adjustment: cats often hide symptoms, so by the time
        # the owner notices something, it may be more urgent
        species = intake_data.get('species', '').lower()
        if species == 'cat':
            high_count += 1
            contributing_factors.append(
                'Cat (may be masking severity)'
            )

        # Map signal count to urgency tier
        urgency_score = high_count - low_count
        if urgency_score >= 4:
            tier = 'Emergency'
        elif urgency_score >= 2:
            tier = 'Same-day'
        elif urgency_score >= 1:
            tier = 'Soon'
        else:
            tier = 'Routine'

        # Confidence is lower for rule-based fallback than LLM primary path
        confidence = min(0.7, 0.4 + (high_count + low_count) * 0.1)

        rationale = (
            f"Based on {high_count} urgency signal(s) and "
            f"{low_count} reassuring signal(s). "
            f"{'Factors: ' + ', '.join(contributing_factors) if contributing_factors else ''}"
        )

        logger.info(
            f"Triage result: {tier} (score={urgency_score}, "
            f"confidence={confidence:.2f})"
        )

        return {
            'agent_name': self.agent_name,
            'status': 'success',
            'output': {
                'urgency_tier': tier,
                'rationale': rationale.strip(),
                'confidence': confidence,
                'contributing_factors': contributing_factors
            },
            'confidence': confidence,
            'warnings': (
                ['Using rule-based fallback — LLM call failed']
                if confidence < 0.6 else []
            )
        }
