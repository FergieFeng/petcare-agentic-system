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

        if self.session.get('state') in ('complete', 'emergency', 'booked'):
            return self._handle_post_completion(user_message)

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
                         'cockatiel', 'canary', 'finch', 'macaw', 'cockatoo',
                         'chicken', 'chickens', 'rooster', 'hen', 'duck',
                         'ducks', 'goose', 'geese', 'turkey', 'pigeon',
                         'dove', 'lovebird', 'conure', 'african grey'],
                'rabbit': ['rabbit', 'rabbits', 'bunny', 'bunnies', 'hare'],
                'hamster': ['hamster', 'hamsters', 'gerbil', 'guinea pig'],
                'reptile': ['reptile', 'lizard', 'gecko', 'iguana', 'snake',
                            'turtle', 'tortoise', 'bearded dragon', 'chameleon'],
                'horse': ['horse', 'horses', 'pony', 'ponies', 'foal',
                          'mare', 'stallion', 'colt', 'filly'],
                'fish': ['fish', 'goldfish', 'betta', 'guppy', 'koi',
                         'aquarium fish', 'tropical fish'],
                'other': ['hedgehog', 'chinchilla', 'rat', 'rats',
                          'mouse', 'mice', 'ferret', 'ferrets',
                          'frog', 'toad', 'goat', 'sheep', 'pig',
                          'piglet', 'cow', 'calf', 'lamb'],
            }
            # Build search text from user message + all prior user messages
            all_user_text = user_message.lower()
            for msg in self.session.get('messages', []):
                if msg.get('role') == 'user':
                    all_user_text += ' ' + str(msg.get('content', '')).lower()

            detected_species = None
            matched_keyword = None
            for species_name, keywords in _species_keywords.items():
                for kw in keywords:
                    if kw in all_user_text:
                        detected_species = species_name
                        matched_keyword = kw
                        break
                if detected_species:
                    break

            if detected_species:
                final_name = matched_keyword if matched_keyword not in (
                    'bird', 'birds', 'reptile', 'other'
                ) else detected_species
                intake_out['species'] = final_name
                self.session.setdefault('pet_profile', {})['species'] = final_name
                intake_out.setdefault('pet_profile', {})['species'] = final_name

        species_val = intake_out.get('species') or session_profile.get('species', '')
        has_species = bool(species_val)

        raw_complaint = (
            intake_out.get('chief_complaint')
            or session_symptoms.get('chief_complaint')
            or ''
        )
        has_complaint = bool(raw_complaint) and self.intake_agent._is_real_complaint(
            raw_complaint, species_val
        )

        # If the LLM's complaint fails validation, try the raw user message
        if not has_complaint and user_message.strip():
            if self.intake_agent._is_real_complaint(user_message.strip(), species_val):
                raw_complaint = user_message.strip()
                intake_out['chief_complaint'] = raw_complaint
                self.session.setdefault('symptoms', {})['chief_complaint'] = raw_complaint
                has_complaint = True

        # Track how many times we've asked for clarification to prevent loops
        clarification_count = self.session.get('clarification_count', 0)

        # After 2 failed clarifications, accept whatever the user said and proceed
        if has_species and not has_complaint and clarification_count >= 2 and user_message.strip():
            raw_complaint = user_message.strip()
            intake_out['chief_complaint'] = raw_complaint
            self.session.setdefault('symptoms', {})['chief_complaint'] = raw_complaint
            has_complaint = True
            logger.info(f"Forcing intake complete after {clarification_count} clarifications")

        if has_species and has_complaint:
            intake_out['intake_complete'] = True
            intake_out['follow_up_questions'] = []
            intake_out['species'] = species_val
            intake_out['chief_complaint'] = raw_complaint
            self.session['clarification_count'] = 0
        else:
            self.session['clarification_count'] = clarification_count + 1
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
                    message="Thanks! What symptoms or concerns are you noticing with your pet?",
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

    # ------------------------------------------------------------------
    # Post-completion: appointment confirmation, new session, follow-ups
    # ------------------------------------------------------------------
    _RESTART_KEYWORDS = {
        'start over', 'new session', 'reset', 'another pet',
        'different pet', 'new concern', 'begin again', 'restart',
    }
    _BOOK_KEYWORDS = {
        'book', 'confirm', 'schedule', 'yes', 'okay', 'ok',
        'that one', 'first', 'second', 'third', '1st', '2nd', '3rd',
        'sounds good', 'go ahead', 'please book',
    }

    def _handle_post_completion(self, user_message: str) -> dict:
        msg_lower = user_message.lower().strip()

        if any(kw in msg_lower for kw in self._RESTART_KEYWORDS):
            for key in list(self.session.keys()):
                if key not in ('id', 'language'):
                    del self.session[key]
            self.session['state'] = 'intake'
            self.session['messages'] = []
            self.session['agent_outputs'] = {}
            return self._build_response(
                message=(
                    "No problem — let's start fresh!\n\n"
                    "What type of pet do you have (dog, cat, or other)?"
                ),
                state='intake',
                agents=[]
            )

        sched_out = self.session.get('agent_outputs', {}).get('scheduling', {}).get('output', {})
        slots = sched_out.get('proposed_slots', [])

        # Try to match a slot first — if user mentions a provider, day, or
        # time that matches, that IS booking intent even without "book"/"yes".
        chosen = self._match_slot(msg_lower, slots) if slots else None

        if chosen:
            dt_str = chosen.get('datetime', '')
            try:
                dt = datetime.fromisoformat(dt_str)
                friendly = dt.strftime('%A, %B %d at %I:%M %p')
            except (ValueError, TypeError):
                friendly = dt_str
            provider = chosen.get('provider', 'your veterinarian')
            self.session['state'] = 'booked'
            self.session['booked_slot'] = chosen
            species = self.session.get('pet_profile', {}).get('species', 'pet')
            return self._build_response(
                message=(
                    f"Your appointment has been confirmed:\n\n"
                    f"  **{friendly}** with **{provider}**\n\n"
                    f"Please bring your {species} and any relevant medical records. "
                    f"If symptoms worsen before the appointment, seek emergency care immediately.\n\n"
                    f"Would you like to start a new session for another concern? "
                    f"Just say **\"start over\"**."
                ),
                state='booked',
                agents=['booking_confirmation']
            )

        # User said a booking keyword but we couldn't match a specific slot
        if any(kw in msg_lower for kw in self._BOOK_KEYWORDS) and slots:
            slot_lines = []
            for i, s in enumerate(slots[:3], 1):
                dt_str = s.get('datetime', '')
                try:
                    dt = datetime.fromisoformat(dt_str)
                    friendly = dt.strftime('%A, %B %d at %I:%M %p')
                except (ValueError, TypeError):
                    friendly = dt_str
                slot_lines.append(f"  {i}. {friendly} with {s.get('provider')}")
            return self._build_response(
                message=(
                    "Which appointment would you like to book? "
                    "Please pick one:\n\n" + '\n'.join(slot_lines)
                ),
                state='complete',
                agents=[]
            )

        if self.session.get('state') == 'booked':
            return self._build_response(
                message=(
                    "Your appointment is already booked! "
                    "If you'd like to start a new session, just say **\"start over\"**."
                ),
                state='booked',
                agents=[]
            )

        if slots:
            slot_lines = []
            for i, s in enumerate(slots[:3], 1):
                dt_str = s.get('datetime', '')
                try:
                    dt = datetime.fromisoformat(dt_str)
                    friendly = dt.strftime('%A, %B %d at %I:%M %p')
                except (ValueError, TypeError):
                    friendly = dt_str
                slot_lines.append(f"  {i}. {friendly} with {s.get('provider')}")
            return self._build_response(
                message=(
                    "Would you like to book one of these appointments?\n\n"
                    + '\n'.join(slot_lines) +
                    "\n\nJust say which one (e.g. **\"book the first one\"** or **\"Tuesday with Dr. Patel\"**), "
                    "or say **\"start over\"** for a new concern."
                ),
                state='complete',
                agents=[]
            )

        return self._build_response(
            message=(
                "Your triage is complete. You can say **\"start over\"** "
                "to begin a new session for a different concern."
            ),
            state='complete',
            agents=[]
        )

    def _match_slot(self, msg: str, slots: list) -> dict | None:
        """Best-effort matching of user message to a proposed slot."""
        # 1. Ordinal references ("first", "1", "2nd", etc.)
        ordinals = {'first': 0, '1st': 0, '1': 0, 'second': 1, '2nd': 1, '2': 1,
                    'third': 2, '3rd': 2, '3': 2}
        for word, idx in ordinals.items():
            if word in msg and idx < len(slots):
                return slots[idx]

        # 2. Score each slot by how many components match the message
        import re
        best_slot = None
        best_score = 0
        for s in slots:
            score = 0
            dt_str = s.get('datetime', '')
            provider = s.get('provider', '').lower()
            try:
                dt = datetime.fromisoformat(dt_str)
                # Day name match (e.g. "tuesday")
                if dt.strftime('%A').lower() in msg:
                    score += 2
                # Month name match (e.g. "march")
                if dt.strftime('%B').lower() in msg:
                    score += 1
                # Day-of-month match (e.g. "10th", "10")
                day_num = str(dt.day)
                if re.search(rf'\b{day_num}(?:st|nd|rd|th)?\b', msg):
                    score += 1
                # Hour match (e.g. "11 am", "11am", "2 pm")
                hour_12 = dt.hour % 12 or 12
                ampm = 'am' if dt.hour < 12 else 'pm'
                if re.search(rf'\b{hour_12}\s*{ampm}\b', msg):
                    score += 2
                elif re.search(rf'\b{hour_12}\b', msg):
                    score += 1
            except (ValueError, TypeError):
                pass
            # Provider name match
            if provider and provider in msg:
                score += 3
            else:
                last_name = provider.split()[-1] if provider else ''
                if last_name and last_name in msg:
                    score += 3
            if score > best_score:
                best_score = score
                best_slot = s

        if best_score >= 2:
            return best_slot

        # 3. Single slot — just book it
        if len(slots) == 1:
            return slots[0]
        return None

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
