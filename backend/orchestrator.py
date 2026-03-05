"""
PetCare Triage & Smart Booking Agent -- Orchestrator

Authors: Syed Ali Turab, Fergie Feng & Diana Liu | Team: Broadview
Date:   March 1, 2026
Code updated: Syed Ali Turab, March 4, 2026 — owner message no longer includes triage rationale (clinic-only).

Central coordinator for the 7 sub-agent pipeline:
  A. Intake → B. Safety Gate → C. Confidence Gate →
  D. Triage → E. Routing → F. Scheduling → G. Guidance & Summary

The Orchestrator is responsible for:
  1. Workflow control -- executing agents in the correct order with branching
  2. Session state management -- maintaining context across all sub-agents
  3. Safety enforcement -- ensuring red flags always trigger escalation
  4. Decision arbitration -- resolving conflicts between agent outputs
  5. Output assembly -- combining all agent results into the final response

Branching logic:
  - If Safety Gate (B) detects a red flag → EMERGENCY path → skip to G
  - If Confidence Gate (C) has low confidence → CLARIFY loop (back to A, max 2x)
  - If Scheduling (F) finds no slots → generate manual booking request
  - Normal path: A → B → C → D → E → F → G
"""

import time
import logging
from datetime import datetime

# Sub-agent imports (each agent is a separate module with a single class)
from agents.intake_agent import IntakeAgent
from agents.safety_gate_agent import SafetyGateAgent
from agents.confidence_gate import ConfidenceGateAgent
from agents.triage_agent import TriageAgent
from agents.routing_agent import RoutingAgent
from agents.scheduling_agent import SchedulingAgent
from agents.guidance_summary import GuidanceSummaryAgent

logger = logging.getLogger('petcare.orchestrator')


class Orchestrator:
    """
    Central coordinator for the PetCare sub-agent pipeline.

    The Orchestrator manages the end-to-end intake flow:

    1. Receives owner messages (text or voice-transcribed)
    2. Routes through the appropriate sub-agent based on current state
    3. Enforces safety invariants (red flags → immediate escalation)
    4. Manages clarification loops when data is incomplete
    5. Assembles the final owner-facing response and clinic-facing summary

    Attributes:
        session (dict): The active session data (pet profile, symptoms,
                        messages, agent outputs, state).
        config (dict): Optional configuration overrides (model, thresholds).
        start_time (float): Timestamp when processing began (for latency tracking).
        MAX_CLARIFICATION_LOOPS (int): Maximum times we can loop back to
                                       Intake for missing info before routing
                                       to a human receptionist.
    """

    # Safety limit: prevent infinite clarification loops.
    # After 2 loops, route to human receptionist review.
    MAX_CLARIFICATION_LOOPS = 2

    def __init__(self, session: dict, config: dict = None):
        """
        Initialize the Orchestrator with a session and optional config.

        Args:
            session: Dict containing the active session state. Must have
                     keys: id, state, pet_profile, symptoms, messages,
                     agent_outputs, clarification_count.
            config: Optional dict with overrides (e.g., model name,
                    confidence thresholds, data file paths).
        """
        self.session = session
        self.config = config or {}
        self.start_time = None

        # Initialize all sub-agents.
        # Data file paths can be overridden via config.
        self.intake_agent = IntakeAgent()
        self.safety_gate = SafetyGateAgent(
            red_flags_path=self.config.get('red_flags_path')
        )
        self.confidence_gate = ConfidenceGateAgent()
        self.triage_agent = TriageAgent()
        self.routing_agent = RoutingAgent(
            clinic_rules_path=self.config.get('clinic_rules_path')
        )
        self.scheduling_agent = SchedulingAgent(
            slots_path=self.config.get('slots_path')
        )
        self.guidance_agent = GuidanceSummaryAgent()

    def process(self, user_message: str) -> dict:
        self.start_time = time.time()
        agents_executed = []

        # Step 1: INTAKE AGENT
        intake_result = self.intake_agent.process(self.session, user_message)
        agents_executed.append('intake')
        self.session['agent_outputs']['intake'] = intake_result

        # Enrich intake_out with everything known from session so far.
        # The LLM may only extract fields from the current message —
        # we must carry forward what prior turns already established.
        intake_out = intake_result['output']
        session_profile = self.session.get('pet_profile', {})
        session_symptoms = self.session.get('symptoms', {})

        if not intake_out.get('species') and session_profile.get('species'):
            intake_out['species'] = session_profile['species']
        if not intake_out.get('chief_complaint') and session_symptoms.get('chief_complaint'):
            intake_out['chief_complaint'] = session_symptoms['chief_complaint']
        # If chief_complaint is still empty, use the raw user message as fallback.
        # The LLM sometimes files symptoms into symptom_details.additional but
        # leaves chief_complaint blank — the user's message is always a valid complaint.
        if not intake_out.get('chief_complaint') and user_message.strip():
            intake_out['chief_complaint'] = user_message.strip()
            self.session.setdefault('symptoms', {})['chief_complaint'] = user_message.strip()
        if not intake_out.get('pet_profile'):
            intake_out['pet_profile'] = session_profile
        if not intake_out.get('symptom_details', {}).get('area') and session_symptoms.get('area'):
            intake_out.setdefault('symptom_details', {})['area'] = session_symptoms['area']

        # Species keyword fallback: if LLM left species empty, scan the
        # user message and full conversation history for species keywords.
        # This handles "my dog", "my cat", "our puppy" etc.
        if not intake_out.get('species') and not session_profile.get('species'):
            _species_keywords = {
                'dog': ['dog', 'dogs', 'puppy', 'puppies', 'pup', 'pups',
                        'canine', 'hound', 'labrador', 'retriever', 'bulldog',
                        'poodle', 'beagle', 'husky', 'shepherd', 'dachshund',
                        'chihuahua', 'rottweiler', 'doberman', 'pitbull',
                        'chien', 'chienne', 'chiot',
                        'perro', 'perra', 'perrito',
                        'hund', 'welpe',
                        'cane', 'cagnolino'],
                'cat': ['cat', 'cats', 'kitten', 'kittens', 'kitty', 'kitties',
                        'feline', 'tabby', 'calico', 'siamese', 'persian',
                        'bengal', 'maine coon', 'ragdoll',
                        'chat', 'chatte', 'chaton',
                        'gato', 'gata', 'gatito',
                        'katze', 'kätzchen',
                        'gatto', 'gattino'],
                'bird': ['bird', 'birds', 'parrot', 'parakeet', 'budgie',
                         'cockatiel', 'canary', 'finch', 'macaw', 'cockatoo'],
                'rabbit': ['rabbit', 'rabbits', 'bunny', 'bunnies', 'hare'],
                'hamster': ['hamster', 'hamsters', 'gerbil', 'guinea pig'],
                'reptile': ['reptile', 'lizard', 'gecko', 'iguana', 'snake',
                            'turtle', 'tortoise', 'bearded dragon'],
            }
            # Build search text from user message + all prior user messages
            all_user_text = user_message.lower()
            for msg in self.session.get('messages', []):
                if msg.get('role') == 'user':
                    all_user_text += ' ' + str(msg.get('content', '')).lower()

            detected_species = None
            for species_name, keywords in _species_keywords.items():
                if any(kw in all_user_text for kw in keywords):
                    detected_species = species_name
                    break

            if detected_species:
                intake_out['species'] = detected_species
                self.session.setdefault('pet_profile', {})['species'] = detected_species
                intake_out.setdefault('pet_profile', {})['species'] = detected_species

        # Authoritative completion check.
        # We only need species + chief_complaint to proceed safely.
        # The LLM is not allowed to block triage by asking optional
        # questions (age, weight, breed) when required fields are known.
        has_species = bool(
            intake_out.get('species') or session_profile.get('species')
        )
        has_complaint = bool(
            intake_out.get('chief_complaint') or session_symptoms.get('chief_complaint')
        )

        if has_species and has_complaint:
            # Minimum fields met — force intake complete regardless of LLM.
            intake_out['intake_complete'] = True
            intake_out['follow_up_questions'] = []
            intake_out['species'] = (
                intake_out.get('species') or session_profile.get('species')
            )
            intake_out['chief_complaint'] = (
                intake_out.get('chief_complaint') or session_symptoms.get('chief_complaint')
            )
        else:
            # Missing required fields — ask for them and stop here.
            follow_ups = intake_out.get('follow_up_questions', [])
            if follow_ups:
                q = follow_ups[0]
                if isinstance(q, dict):
                    q = q.get('question') or q.get('text') or str(q)
                return self._build_response(
                    message=q,
                    state='intake',
                    agents=agents_executed
                )
            elif not has_species:
                return self._build_response(
                    message='What type of pet do you have? (dog, cat, or other)',
                    state='intake',
                    agents=agents_executed
                )
            else:
                return self._build_response(
                    message='Can you describe the main symptom you are concerned about?',
                    state='intake',
                    agents=agents_executed
                )

        # Step 2: SAFETY GATE
        safety_result = self.safety_gate.process(intake_out)
        agents_executed.append('safety_gate')
        self.session['agent_outputs']['safety_gate'] = safety_result

        if safety_result['output']['red_flag_detected']:
            self.session['state'] = 'emergency'
            logger.warning(
                f"RED FLAG DETECTED in session {self.session['id']}: "
                f"{safety_result['output']['red_flags']}"
            )
            guidance_result = self.guidance_agent.process(
                self.session, self.session['agent_outputs']
            )
            agents_executed.append('guidance_summary')
            self.session['agent_outputs']['guidance_summary'] = guidance_result
            return self._build_response(
                message=safety_result['output']['escalation_message'],
                state='emergency',
                agents=agents_executed,
                emergency=True
            )

        # Step 3: CONFIDENCE GATE
        confidence_result = self.confidence_gate.process(intake_out)
        agents_executed.append('confidence_gate')
        self.session['agent_outputs']['confidence_gate'] = confidence_result

        if confidence_result['output']['action'] == 'clarify':
            loop_count = self.session.get('clarification_count', 0)
            if loop_count < self.MAX_CLARIFICATION_LOOPS:
                self.session['clarification_count'] = loop_count + 1
                missing = confidence_result['output'].get('missing_required', [])
                return self._build_response(
                    message=(
                        f"I need a bit more information to help you. "
                        f"Could you tell me about: {', '.join(missing)}?"
                    ),
                    state='intake',
                    agents=agents_executed
                )
            else:
                return self._build_response(
                    message=(
                        "I want to make sure your pet gets the right care. "
                        "Let me connect you with our receptionist who can "
                        "help complete the intake. One moment please."
                    ),
                    state='human_review',
                    agents=agents_executed
                )
        elif confidence_result['output']['action'] == 'human_review':
            return self._build_response(
                message=(
                    "Some of the information seems conflicting. "
                    "Let me connect you with our receptionist to ensure "
                    "we get the most accurate assessment."
                ),
                state='human_review',
                agents=agents_executed
            )

        # Step 4: TRIAGE AGENT
        triage_result = self.triage_agent.process(intake_out, safety_result)
        agents_executed.append('triage')
        self.session['agent_outputs']['triage'] = triage_result

        # Step 5: ROUTING AGENT
        routing_result = self.routing_agent.process(intake_out, triage_result)
        agents_executed.append('routing')
        self.session['agent_outputs']['routing'] = routing_result

        # Step 6: SCHEDULING AGENT
        scheduling_result = self.scheduling_agent.process(
            routing_result, triage_result
        )
        agents_executed.append('scheduling')
        self.session['agent_outputs']['scheduling'] = scheduling_result

        # Step 7: GUIDANCE & SUMMARY AGENT
        guidance_result = self.guidance_agent.process(
            self.session, self.session['agent_outputs']
        )
        agents_executed.append('guidance_summary')
        self.session['agent_outputs']['guidance_summary'] = guidance_result

        self.session['state'] = 'complete'

        urgency = triage_result['output'].get('urgency_tier', 'Routine')
        rationale = triage_result['output'].get('rationale', '')
        guidance = guidance_result['output'].get('owner_guidance', {})
        slots = scheduling_result['output'].get('proposed_slots', [])

        message_parts = [
            f"Based on what you've told me, I'd recommend a **{urgency}** visit.",
        ]

        if slots:
            message_parts.append("\nAvailable appointments:")
            for s in slots[:3]:
                dt_str = s.get('datetime', '')
                try:
                    dt = datetime.fromisoformat(dt_str)
                    friendly = dt.strftime('%A, %B %d at %I:%M %p')
                except (ValueError, TypeError):
                    friendly = dt_str
                message_parts.append(
                    f"  - {friendly} with {s.get('provider')}"
                )

        if guidance.get('do'):
            message_parts.append("\nWhile you wait:")
            for tip in guidance['do'][:3]:
                message_parts.append(f"  ✓ {tip}")

        if guidance.get('watch_for'):
            message_parts.append("\nSeek emergency care if you notice:")
            for warn in guidance['watch_for'][:3]:
                message_parts.append(f"  ⚠ {warn}")

        return self._build_response(
            message='\n'.join(message_parts),
            state='complete',
            agents=agents_executed
        )

    def _build_response(self, message: str, state: str,
                        agents: list, emergency: bool = False) -> dict:
        """
        Build a standardized response dict.

        Args:
            message: The text to display to the pet owner.
            state: The current workflow state after this step.
            agents: List of agent names that were executed.
            emergency: Whether this is an emergency escalation.

        Returns:
            Standardized response dict with message, state, metadata.
        """
        elapsed_ms = int((time.time() - self.start_time) * 1000)
        return {
            'message': message,
            'state': state,
            'session_id': self.session['id'],
            'emergency': emergency,
            'metadata': {
                'processing_time_ms': elapsed_ms,
                'agents_executed': agents
            }
        }
