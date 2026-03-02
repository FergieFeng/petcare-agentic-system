"""
Sub-Agent A: Intake Agent

Authors: Syed Ali Turab & Fergie Feng | Team: Broadview
Date:   March 1, 2026

Collects pet profile, chief complaint, and symptom details through
adaptive, multi-turn follow-up questions tailored to species and symptom area.

This agent is the first in the pipeline and handles the conversational
intake flow. It:
  1. Parses the owner's free-text message for pet profile fields
     (species, breed, age, weight, name)
  2. Identifies the symptom area (GI, respiratory, derm, injury, urinary, etc.)
  3. Asks adaptive follow-up questions specific to the symptom area
  4. Builds a structured output that downstream agents can consume

The intake process is multi-turn: the agent may need 2-5 messages to
collect all required information. The Orchestrator manages the turn loop.

Input:  Owner's free-text message + current session state
Output: Structured pet_profile + symptom_details + follow-up questions
"""

import logging

logger = logging.getLogger('petcare.agents.intake')

# ---------------------------------------------------------------------------
# Field Definitions
# ---------------------------------------------------------------------------

# These fields MUST be collected before we can proceed to triage.
# If missing, the Confidence Gate will flag them.
REQUIRED_FIELDS = ['species', 'chief_complaint']

# These fields improve triage quality but aren't strictly required.
# Missing optional fields lower confidence but don't block the flow.
OPTIONAL_FIELDS = [
    'pet_name', 'breed', 'age', 'weight',
    'timeline', 'eating_drinking', 'energy_level'
]

# ---------------------------------------------------------------------------
# Symptom-Area-Specific Follow-Up Questions
# ---------------------------------------------------------------------------
# When the intake agent identifies a symptom area, it selects the
# appropriate set of follow-up questions. These are designed to collect
# the minimum information needed for accurate triage.
#
# Each area's questions target the key differentiating factors that
# determine urgency (e.g., blood in vomit → higher urgency for GI).

SYMPTOM_AREA_FOLLOWUPS = {
    'gastrointestinal': [
        'How many times has your pet vomited in the last 24 hours?',
        'Is there any diarrhea?',
        'Is there any blood in the vomit or stool?',
        'Could your pet have eaten something unusual (garbage, toys, plants)?'
    ],
    'respiratory': [
        'Is your pet having difficulty breathing or breathing rapidly?',
        'Is there coughing? If so, is it dry or productive?',
        'Any nasal discharge?',
        'Is the cough worse at night or after exercise?'
    ],
    'dermatological': [
        'Where on the body is the skin issue?',
        'Is there itching, redness, or hair loss?',
        'How long has this been going on?',
        'Any new foods, products, or environmental changes recently?'
    ],
    'injury': [
        'Where is the injury located?',
        'Is your pet able to walk/move normally?',
        'Is there swelling or bleeding?',
        'Do you know what caused the injury?'
    ],
    'urinary': [
        'Is your pet straining to urinate?',
        'Is there blood in the urine?',
        'How frequently is your pet trying to urinate?',
        'Is your pet able to produce any urine?'
    ],
    'neurological': [
        'Has your pet had any seizures or tremors?',
        'Is your pet disoriented or walking in circles?',
        'Any head tilting or loss of balance?',
        'How long have these symptoms been occurring?'
    ],
    'behavioral': [
        'What specific behavior changes have you noticed?',
        'When did the changes start?',
        'Has anything in the environment changed recently?',
        'Is your pet eating and drinking normally?'
    ]
}


class IntakeAgent:
    """
    Adaptive symptom intake agent.

    Conducts a structured, multi-turn conversation to collect:
      - Pet profile (species, breed, age, weight, name)
      - Chief complaint (primary symptom description)
      - Symptom details (area-specific information)
      - Timeline (when symptoms started, progression)
      - Context (eating/drinking, energy level, possible triggers)

    The agent adapts its follow-up questions based on:
      - Species (dogs vs cats vs exotic have different common conditions)
      - Symptom area (GI vs respiratory vs injury need different details)
      - What information has already been collected
    """

    def __init__(self):
        """Initialize the Intake Agent."""
        self.agent_name = 'intake'

    def process(self, session: dict, user_message: str) -> dict:
        """
        Process a user message and extract/update intake information.

        This method is called for each message during the intake phase.
        It parses the message for relevant fields, updates the session
        state, and determines whether more information is needed.

        Args:
            session: The current session dict containing pet_profile,
                     symptoms, and conversation history.
            user_message: The owner's latest text input (typed or
                          voice-transcribed).

        Returns:
            dict with standard agent output contract:
              - agent_name (str): 'intake'
              - status (str): 'success' | 'needs_review'
              - output (dict): Contains pet_profile, chief_complaint,
                symptom_details, follow_up_questions, intake_complete
              - confidence (float): 0.0 to 1.0
              - warnings (list): Any issues encountered
        """
        # TODO: Replace this stub with LLM-powered adaptive intake.
        #
        # Implementation plan:
        # 1. Send user_message + conversation history to LLM with a system
        #    prompt that instructs structured extraction
        # 2. LLM returns: extracted fields + identified symptom area +
        #    next follow-up question (or 'intake_complete' if done)
        # 3. Update session.pet_profile and session.symptoms with new fields
        # 4. Return the next question or mark intake as complete
        #
        # The LLM prompt should:
        #   - Extract structured fields from conversational text
        #   - Identify the symptom area for follow-up selection
        #   - Determine when enough info has been collected
        #   - NEVER provide diagnoses or medical advice

        return {
            'agent_name': self.agent_name,
            'status': 'success',
            'output': {
                'pet_profile': {},
                'chief_complaint': user_message,
                'symptom_details': {},
                'follow_up_questions': [],
                'intake_complete': False
            },
            'confidence': 0.0,
            'warnings': ['Intake agent not yet implemented — using stub']
        }
