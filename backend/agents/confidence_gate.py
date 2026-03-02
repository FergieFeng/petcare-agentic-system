"""
Sub-Agent C: Confidence Gate Agent

Authors: Syed Ali Turab & Fergie Feng | Team: Broadview
Date:   March 1, 2026

Validates required intake fields, assesses overall data confidence,
detects conflicting signals, and determines the next action.

This agent acts as a quality checkpoint between intake and triage.
It ensures the data is complete and coherent enough to produce a
reliable triage classification. If not, it either:
  - Requests clarification (loop back to Intake, up to 2 times)
  - Routes to a human receptionist (conflicting signals or max loops)

Confidence scoring formula:
  - Start at 1.0 (fully confident)
  - Subtract 0.3 for each missing REQUIRED field
  - Subtract 0.1 for each missing IMPORTANT field
  - Subtract 0.2 for each detected conflict
  - Clamp to [0.0, 1.0]

Action thresholds:
  - confidence >= 0.6 AND no conflicts → 'proceed' to triage
  - confidence < 0.6 OR missing required → 'clarify' (loop to Intake)
  - conflicts detected → 'human_review' (route to receptionist)

Input:  Structured intake data from the Intake Agent
Output: Confidence score, missing fields, conflicts, recommended action
"""

import logging

logger = logging.getLogger('petcare.agents.confidence_gate')

# ---------------------------------------------------------------------------
# Field Classifications
# ---------------------------------------------------------------------------

# REQUIRED: Must have these to proceed. Without species, we can't apply
# species-specific triage rules. Without chief_complaint, there's nothing
# to triage.
REQUIRED_FIELDS = ['species', 'chief_complaint']

# IMPORTANT: Strongly improve triage accuracy but aren't blocking.
# Missing these lowers confidence and may affect triage quality.
IMPORTANT_FIELDS = ['timeline', 'eating_drinking', 'energy_level']

# CONFLICT PAIRS: Combinations of signals that suggest the owner's
# description may be unreliable or confused. When detected, route
# to human review rather than relying on automated triage.
CONFLICT_PAIRS = [
    # If the pet isn't breathing, it can't be acting normal
    (['not breathing', 'can\'t breathe'], ['acting normal', 'seems fine']),
    # Collapse and running around are contradictory
    (['collapsed', 'collapse'], ['running around', 'playing']),
]


class ConfidenceGateAgent:
    """
    Field validation and confidence assessment agent.

    Checks three dimensions of data quality:
      1. Completeness: Are all required and important fields present?
      2. Coherence: Are there any conflicting signals in the data?
      3. Sufficiency: Is there enough detail for accurate triage?

    Based on the assessment, recommends one of three actions:
      - 'proceed': Data is good enough for triage
      - 'clarify': Need more information (loop to Intake)
      - 'human_review': Data is conflicting (route to receptionist)
    """

    def __init__(self):
        """Initialize the Confidence Gate Agent."""
        self.agent_name = 'confidence_gate'

    def process(self, intake_data: dict) -> dict:
        """
        Validate intake data completeness, coherence, and confidence.

        Performs three checks:
          1. Required field presence (species, chief_complaint)
          2. Important field presence (timeline, eating/drinking, energy)
          3. Conflict detection (contradictory symptom descriptions)

        Then computes a confidence score and recommends an action.

        Args:
            intake_data: Dict from the Intake Agent containing
                pet_profile, chief_complaint, symptom_details, etc.

        Returns:
            dict with standard agent output contract:
              - agent_name (str): 'confidence_gate'
              - status (str): 'success' | 'needs_review'
              - output (dict): confidence_score, missing_required,
                missing_important, conflicts, action
              - confidence (float): Same as confidence_score
              - warnings (list): One warning per missing required field
        """
        missing_required = []
        missing_important = []
        conflicts = []

        # ----- Check 1: Required field presence -----
        for field in REQUIRED_FIELDS:
            if not intake_data.get(field):
                missing_required.append(field)

        # ----- Check 2: Important field presence -----
        for field in IMPORTANT_FIELDS:
            if not intake_data.get(field):
                missing_important.append(field)

        # ----- Check 3: Conflict detection -----
        # Look for contradictory signals in the combined text.
        # If both sides of a conflict pair are present, flag it.
        combined_text = (
            intake_data.get('chief_complaint', '') + ' ' +
            str(intake_data.get('symptom_details', ''))
        ).lower()

        for red_signals, green_signals in CONFLICT_PAIRS:
            has_red = any(s in combined_text for s in red_signals)
            has_green = any(s in combined_text for s in green_signals)
            if has_red and has_green:
                conflicts.append(
                    f"Conflicting signals: '{red_signals[0]}' "
                    f"vs '{green_signals[0]}'"
                )

        # ----- Compute confidence score -----
        # Scoring: start at 1.0, subtract for missing/conflicting data.
        # Each missing required field is a major penalty (0.3).
        # Each missing important field is a minor penalty (0.1).
        # Each conflict is a significant penalty (0.2).
        completeness = 1.0 - (
            len(missing_required) * 0.3 +
            len(missing_important) * 0.1 +
            len(conflicts) * 0.2
        )
        completeness = max(0.0, min(1.0, completeness))

        # ----- Determine action -----
        if missing_required:
            # Can't proceed without required fields
            action = 'clarify'
            status = 'needs_review'
        elif conflicts:
            # Conflicting data needs human judgment
            action = 'human_review'
            status = 'needs_review'
        elif completeness < 0.6:
            # Too much missing data for reliable triage
            action = 'clarify'
            status = 'needs_review'
        else:
            # Data is sufficient — proceed to triage
            action = 'proceed'
            status = 'success'

        if action != 'proceed':
            logger.info(
                f"Confidence gate: action={action}, score={completeness:.2f}, "
                f"missing_req={missing_required}, conflicts={conflicts}"
            )

        return {
            'agent_name': self.agent_name,
            'status': status,
            'output': {
                'confidence_score': completeness,
                'missing_required': missing_required,
                'missing_important': missing_important,
                'conflicts': conflicts,
                'action': action
            },
            'confidence': completeness,
            'warnings': [
                f"Missing required field: {f}" for f in missing_required
            ]
        }
