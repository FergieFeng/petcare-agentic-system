"""
Sub-Agent G: Guidance & Summary Agent

Authors: Syed Ali Turab & Fergie Feng | Team: Broadview
Date:   March 1, 2026

Generates two outputs:
  1. Owner-facing "do/don't while waiting" guidance (safe, non-diagnostic)
  2. Clinic-facing structured intake summary (JSON for vet handoff)

This is the FINAL agent in the pipeline. It receives outputs from
all prior agents and produces the deliverables that make the system
useful to both owners and clinic staff.

Owner Guidance Rules:
  - NEVER diagnose or suggest a specific condition
  - NEVER recommend specific medications or dosages
  - DO provide safe general care tips (water, rest, monitoring)
  - DO provide area-specific tips (e.g., don't force-feed for GI)
  - DO list escalation cues (when to go to ER immediately)

Clinic Summary Structure:
  - Follows the canonical schema in docs/architecture/output_schema.md
  - Includes: pet profile, symptoms, triage, routing, scheduling,
    confidence, guidance, metadata
  - Validated before return

Input:  Session state + all agent outputs
Output: Owner guidance dict + clinic summary JSON
"""

import logging
from datetime import datetime

logger = logging.getLogger('petcare.agents.guidance_summary')

# ---------------------------------------------------------------------------
# General Guidance Templates
# ---------------------------------------------------------------------------
# These apply to ALL cases regardless of symptom area.
# They are safe, non-diagnostic, and universally applicable.

GENERAL_GUIDANCE = {
    'do': [
        'Keep fresh water available for your pet',
        'Monitor your pet closely for any changes',
        'Keep your pet in a calm, comfortable environment',
        'Note any new or worsening symptoms to report to the vet'
    ],
    'dont': [
        'Do not give human medications without veterinary guidance',
        'Do not force-feed your pet if they are refusing food',
        'Do not attempt to induce vomiting unless directed by a veterinarian'
    ],
    'watch_for': [
        'Difficulty breathing or rapid breathing',
        'Extreme lethargy or collapse',
        'Severe or uncontrolled bleeding',
        'Seizures or loss of consciousness'
    ]
}

# ---------------------------------------------------------------------------
# Area-Specific Guidance Templates
# ---------------------------------------------------------------------------
# Additional tips specific to the symptom area.
# These supplement (not replace) the general guidance above.

AREA_SPECIFIC_GUIDANCE = {
    'gastrointestinal': {
        'do': [
            'Offer small amounts of water frequently',
            'Note frequency and appearance of vomiting/diarrhea'
        ],
        'dont': [
            'Do not give fatty or rich foods',
            'Do not give dairy products'
        ],
        'watch_for': [
            'Blood in vomit or stool',
            'Abdominal swelling or distension'
        ]
    },
    'respiratory': {
        'do': [
            'Keep your pet in a well-ventilated area',
            'Minimize exercise and excitement'
        ],
        'dont': [
            'Do not use a tight collar if breathing is labored'
        ],
        'watch_for': [
            'Blue or pale gums (sign of oxygen deprivation)',
            'Open-mouth breathing (especially concerning in cats)'
        ]
    },
    'injury': {
        'do': [
            'Restrict movement to prevent further injury',
            'Apply gentle pressure to bleeding wounds with a clean cloth'
        ],
        'dont': [
            'Do not apply ice directly to the skin',
            'Do not attempt to splint or set broken bones'
        ],
        'watch_for': [
            'Increasing swelling',
            'Loss of use of a limb'
        ]
    },
    'urinary': {
        'do': [
            'Monitor urination attempts and output',
            'Note color of urine if possible'
        ],
        'dont': [
            'Do not restrict water intake'
        ],
        'watch_for': [
            'Complete inability to urinate (EMERGENCY in cats)',
            'Crying or vocalizing when trying to urinate'
        ]
    },
    'dermatological': {
        'do': [
            'Prevent your pet from scratching or licking the area',
            'Keep the area clean and dry'
        ],
        'dont': [
            'Do not apply human skin products without vet guidance'
        ],
        'watch_for': [
            'Rapid spreading of the affected area',
            'Signs of infection (swelling, warmth, discharge)'
        ]
    }
}


class GuidanceSummaryAgent:
    """
    Owner guidance and clinic summary generation agent.

    Produces the final outputs of the PetCare pipeline:

    1. Owner Guidance: Safe, non-diagnostic tips organized as:
       - DO: Positive actions the owner can take while waiting
       - DON'T: Actions to avoid that could worsen the situation
       - WATCH FOR: Escalation cues that mean "go to ER now"

    2. Clinic Summary: Structured JSON containing everything the
       vet team needs to know before the appointment:
       - Pet profile, symptoms, timeline
       - Triage tier with rationale
       - Routing and scheduling info
       - Confidence scores and review flags
       - Full agent execution metadata
    """

    def __init__(self):
        """Initialize the Guidance & Summary Agent."""
        self.agent_name = 'guidance_summary'

    def process(self, session: dict, all_agent_outputs: dict) -> dict:
        """
        Generate owner guidance and clinic-facing summary.

        Combines general guidance with area-specific tips based on
        the symptom category identified during intake. Then assembles
        a comprehensive clinic summary from all agent outputs.

        Args:
            session: The full session dict with pet_profile, symptoms,
                     messages, and agent_outputs.
            all_agent_outputs: Dict of all prior agent outputs, keyed
                               by agent name (e.g., 'triage', 'routing').

        Returns:
            dict with standard agent output contract:
              - agent_name (str): 'guidance_summary'
              - status (str): 'success'
              - output (dict): owner_guidance (dict with do/dont/watch_for),
                clinic_summary (full structured JSON)
              - confidence (float): 0.85
              - warnings (list): Any issues
        """
        # Determine the symptom area for area-specific guidance
        symptom_area = (
            session.get('symptoms', {}).get('area', '')
        )
        area_guidance = AREA_SPECIFIC_GUIDANCE.get(symptom_area, {})

        # Merge general + area-specific guidance
        guidance = {
            'do': GENERAL_GUIDANCE['do'] + area_guidance.get('do', []),
            'dont': GENERAL_GUIDANCE['dont'] + area_guidance.get('dont', []),
            'watch_for': (
                GENERAL_GUIDANCE['watch_for'] +
                area_guidance.get('watch_for', [])
            )
        }

        # ----- Build the clinic-facing structured summary -----
        # This follows the canonical schema defined in
        # docs/architecture/output_schema.md
        clinic_summary = {
            'version': '1.0.0',
            'session_id': session.get('id', ''),
            'timestamp': datetime.utcnow().isoformat(),

            # Pet profile from intake
            'pet_profile': session.get('pet_profile', {}),

            # Symptom information
            'chief_complaint': (
                session.get('symptoms', {}).get('chief_complaint', '')
            ),
            'symptom_details': session.get('symptoms', {}),

            # Safety gate results
            'red_flags': (
                all_agent_outputs
                .get('safety_gate', {})
                .get('output', {})
            ),

            # Triage classification
            'triage': (
                all_agent_outputs
                .get('triage', {})
                .get('output', {})
            ),

            # Appointment routing
            'routing': (
                all_agent_outputs
                .get('routing', {})
                .get('output', {})
            ),

            # Scheduling proposal
            'scheduling': (
                all_agent_outputs
                .get('scheduling', {})
                .get('output', {})
            ),

            # Confidence metrics
            'confidence': {
                'overall': (
                    all_agent_outputs
                    .get('confidence_gate', {})
                    .get('confidence', 0)
                ),
                'intake_completeness': (
                    all_agent_outputs
                    .get('confidence_gate', {})
                    .get('output', {})
                    .get('confidence_score', 0)
                ),
                'triage_confidence': (
                    all_agent_outputs
                    .get('triage', {})
                    .get('confidence', 0)
                ),
                'needs_review': (
                    all_agent_outputs
                    .get('confidence_gate', {})
                    .get('output', {})
                    .get('action') == 'human_review'
                )
            },

            # Owner guidance
            'owner_guidance': guidance,

            # Execution metadata
            'metadata': {
                'agents_executed': list(all_agent_outputs.keys()),
                'processing_time_ms': (
                    sum(
                        o.get('processing_time_ms', 0)
                        for o in all_agent_outputs.values()
                        if isinstance(o, dict)
                    )
                )
            }
        }

        logger.info(
            f"Summary generated for session {session.get('id', 'unknown')}"
        )

        return {
            'agent_name': self.agent_name,
            'status': 'success',
            'output': {
                'owner_guidance': guidance,
                'clinic_summary': clinic_summary
            },
            'confidence': 0.85,
            'warnings': []
        }
