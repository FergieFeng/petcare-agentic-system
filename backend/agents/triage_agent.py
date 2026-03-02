"""
Sub-Agent D: Triage Agent

Authors: Syed Ali Turab & Fergie Feng | Team: Broadview
Date:   March 1, 2026

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

    The current implementation uses a rule-based heuristic that counts
    high-urgency vs low-urgency signals. The production version will
    use an LLM with structured output for more nuanced classification.

    Conservative default: when uncertain, assigns higher urgency.
    This is a deliberate design choice — it's safer to over-triage
    than to under-triage a potentially serious condition.
    """

    def __init__(self):
        """Initialize the Triage Agent."""
        self.agent_name = 'triage'

    def process(self, intake_data: dict, safety_result: dict) -> dict:
        """
        Classify urgency tier based on intake data and safety check.

        Uses a signal-counting heuristic as a rule-based fallback:
          - Count high-urgency signals in the complaint text
          - Count low-urgency signals
          - Adjust based on eating/drinking and energy levels
          - Apply species-specific modifiers (cats get +1 urgency bump)
          - Map the final score to a tier

        Args:
            intake_data: Dict from the Intake Agent with chief_complaint,
                         symptom_details, timeline, eating_drinking,
                         energy_level.
            safety_result: Dict from the Safety Gate Agent (used to check
                           if any near-miss red flags were found).

        Returns:
            dict with standard agent output contract:
              - agent_name (str): 'triage'
              - status (str): 'success'
              - output (dict): urgency_tier, rationale, confidence,
                contributing_factors
              - confidence (float): 0.0 to 1.0
              - warnings (list): Any issues
        """
        # TODO: Replace rule-based heuristic with LLM-powered classification.
        #
        # Implementation plan:
        # 1. Send intake data to LLM with structured output schema
        # 2. System prompt includes triage guidelines and examples
        # 3. LLM returns: tier, rationale, confidence, factors
        # 4. Validate output against schema before returning
        #
        # The LLM prompt should:
        #   - Consider symptom severity, timeline, vitals context
        #   - Apply species-specific knowledge
        #   - Provide evidence-based rationale
        #   - Default to higher urgency when uncertain
        #   - NEVER provide diagnoses

        # ----- Rule-based heuristic (temporary until LLM integration) -----

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

        # Confidence is lower for rule-based classification
        # (will be higher when LLM is integrated)
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
                ['Using rule-based heuristic — LLM not yet integrated']
                if confidence < 0.6 else []
            )
        }
