"""
Sub-Agent A: Intake Agent

Authors: Syed Ali Turab, Fergie Feng & Diana Liu | Team: Broadview
Date:   March 1, 2026
Code updated: Syed Ali Turab, March 4, 2026 — LLM-powered intake
with diagnosis guardrails.
"""

import os
import json
import logging
import openai

logger = logging.getLogger('petcare.agents.intake')

REQUIRED_FIELDS = ['species', 'chief_complaint']
OPTIONAL_FIELDS = ['pet_name', 'breed', 'age', 'weight',
                   'timeline', 'eating_drinking', 'energy_level']


class IntakeAgent:
    """LLM-powered adaptive symptom intake agent."""

    def __init__(self):
        self.agent_name = 'intake'

    _SPECIES_WORDS = {
        'dog', 'cat', 'bird', 'rabbit', 'hamster', 'reptile', 'fish',
        'parrot', 'puppy', 'kitten', 'bunny', 'turtle', 'snake', 'lizard',
        'guinea pig', 'gerbil', 'ferret', 'pet', 'animal',
    }
    _NOISE_PHRASES = {
        'i have a', 'i got a', 'my pet is', 'we have a', 'it is a',
        'she is a', 'he is a', 'its a', "it's a",
    }

    @classmethod
    def _is_real_complaint(cls, complaint: str, species: str = '') -> bool:
        """Return True only if complaint describes an actual health concern."""
        if not complaint:
            return False
        text = complaint.lower().strip()
        if len(text) < 4:
            return False
        for phrase in cls._NOISE_PHRASES:
            text = text.replace(phrase, '')
        for word in cls._SPECIES_WORDS:
            text = text.replace(word, '')
        if species:
            text = text.replace(species.lower(), '')
        cleaned = text.strip(' .,;!?')
        return len(cleaned) >= 3

    def process(self, session: dict, user_message: str) -> dict:
        """
        Extract structured intake data from the owner message via LLM.
        Sets intake_complete=True as soon as species + chief_complaint
        are both known. Never diagnoses or names conditions.
        Falls back to simple extraction on LLM failure.
        """
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        lang_code = session.get('language', 'en')
        lang_names = {
            'en': 'English', 'fr': 'French', 'zh': 'Chinese (Mandarin)',
            'ar': 'Arabic', 'es': 'Spanish', 'hi': 'Hindi', 'ur': 'Urdu'
        }
        lang_name = lang_names.get(lang_code, 'English')

        known_species = session.get('pet_profile', {}).get('species', '')
        known_complaint = session.get('symptoms', {}).get('chief_complaint', '')

        system_prompt = f"""You are a veterinary intake assistant collecting pet symptom information.

HARD RULES — never violate:
1. NEVER name a disease, condition, or diagnosis
2. NEVER suggest medications or dosages
3. NEVER say "your pet has", "this sounds like", "this could be"
4. ONLY collect: species, symptoms as described, duration, eating/drinking, energy level
5. Do NOT comment on urgency at all
6. Respond in {lang_name}. JSON keys must stay in English.
7. Respond ONLY with valid JSON. No markdown fences. No text outside the JSON.

Already known from prior messages — do NOT ask for these again:
  species: "{known_species}"
  chief_complaint: "{known_complaint}"

You must respond with EXACTLY this JSON structure:
{{
  "pet_profile": {{"species": "", "pet_name": "", "breed": "", "age": "", "weight": ""}},
  "chief_complaint": "",
  "symptom_details": {{"area": "", "timeline": "", "eating_drinking": "", "energy_level": "", "additional": ""}},
  "follow_up_questions": [],
  "intake_complete": false
}}

Rules for intake_complete:
- Set intake_complete to TRUE only when species AND a REAL chief_complaint are BOTH known
- chief_complaint must describe a HEALTH CONCERN, SYMPTOM, or REASON FOR VISIT
- "I have a dog", "I have a cat", "my pet is a dog" — these identify species only, NOT chief_complaint. Ask what symptoms or concerns they have.
- "general checkup", "routine visit", "wellness check" ARE valid chief complaints
- "vomiting for 2 days", "limping", "not eating" ARE valid chief complaints
- If the user ONLY told you their species and nothing about health: set intake_complete to false and ask about symptoms
- If species is already "{known_species}" — it is known, do not ask again
- If chief_complaint is already "{known_complaint}" — it is known, do not ask again
- If BOTH are known right now, set intake_complete to true and follow_up_questions to []
- Only set intake_complete to false if you still need species OR a real chief_complaint
- follow_up_questions must be a list containing at most ONE plain string
- NEVER put objects in follow_up_questions
- WRONG: [{{"question": "How old is your pet?"}}]
- RIGHT: ["How old is your pet?"]

For symptom_details.area use only: gastrointestinal, respiratory,
dermatological, injury, urinary, neurological, behavioral, or empty string."""

        history = []
        for msg in session.get('messages', []):
            role = msg.get('role')
            if role not in ('user', 'assistant'):
                continue
            content = msg.get('content', '')
            if isinstance(content, dict):
                content = content.get('question') or content.get('text') or str(content)
            history.append({'role': role, 'content': str(content)})
        history.append({'role': 'user', 'content': user_message})

        try:
            resp = client.chat.completions.create(
                model='gpt-4o-mini',
                max_tokens=500,
                temperature=0.1,
                messages=[{'role': 'system', 'content': system_prompt}] + history
            )
            raw = resp.choices[0].message.content.strip()
            if '```' in raw:
                parts = raw.split('```')
                for part in parts:
                    part = part.strip()
                    if part.startswith('json'):
                        part = part[4:].strip()
                    if part.startswith('{'):
                        raw = part
                        break
            raw = raw.strip()

            parsed = json.loads(raw)

            pet_profile = parsed.get('pet_profile', {})
            symptom_details = parsed.get('symptom_details', {})
            chief_complaint = parsed.get('chief_complaint', '') or known_complaint
            intake_complete = bool(parsed.get('intake_complete', False))
            raw_questions = parsed.get('follow_up_questions', [])

            # Flatten any dict questions the LLM returned despite instructions
            follow_up_questions = []
            for q in raw_questions:
                if isinstance(q, dict):
                    follow_up_questions.append(
                        q.get('question') or q.get('text') or str(q)
                    )
                elif isinstance(q, str) and q.strip():
                    follow_up_questions.append(q.strip())

            # Merge species into session
            species = (pet_profile.get('species') or known_species or '').lower().strip()
            if species:
                session.setdefault('pet_profile', {})['species'] = species
                pet_profile['species'] = species

            # Merge other profile fields
            for k, v in pet_profile.items():
                if v and k != 'species':
                    session.setdefault('pet_profile', {})[k] = v

            # Merge complaint and symptom details into session
            if chief_complaint:
                session.setdefault('symptoms', {})['chief_complaint'] = chief_complaint
            for k, v in symptom_details.items():
                if v:
                    session.setdefault('symptoms', {})[k] = v

            final_species = session.get('pet_profile', {}).get('species', '')
            final_complaint = session.get('symptoms', {}).get('chief_complaint', '')

            if final_species and final_complaint and self._is_real_complaint(final_complaint, final_species):
                intake_complete = True
                follow_up_questions = []

            if not intake_complete and not follow_up_questions:
                if not final_species:
                    follow_up_questions = ['What type of pet do you have? (dog, cat, or other)']
                elif not final_complaint or not self._is_real_complaint(final_complaint, final_species):
                    follow_up_questions = [
                        "Thanks! What symptoms or concerns are you noticing with your pet?"
                    ]

            return {
                'agent_name': self.agent_name,
                'status': 'success',
                'output': {
                    'pet_profile': session.get('pet_profile', {}),
                    'species': final_species,
                    'chief_complaint': final_complaint,
                    'symptom_details': symptom_details,
                    'follow_up_questions': follow_up_questions,
                    'intake_complete': intake_complete
                },
                'confidence': 0.85 if intake_complete else 0.5,
                'warnings': []
            }

        except Exception as e:
            logger.error(f'Intake LLM error: {e}')
            final_species = session.get('pet_profile', {}).get('species', '')
            candidate = session.get('symptoms', {}).get('chief_complaint', '') or user_message
            if self._is_real_complaint(candidate, final_species):
                final_complaint = candidate
                session.setdefault('symptoms', {})['chief_complaint'] = final_complaint
            else:
                final_complaint = ''
            complete = bool(final_species and final_complaint)
            fq = []
            if not final_species:
                fq = ['What type of pet do you have? (dog, cat, or other)']
            elif not final_complaint:
                fq = ['Thanks! What symptoms or concerns are you noticing with your pet?']
            return {
                'agent_name': self.agent_name,
                'status': 'success',
                'output': {
                    'pet_profile': session.get('pet_profile', {}),
                    'species': final_species,
                    'chief_complaint': final_complaint,
                    'symptom_details': {},
                    'follow_up_questions': fq,
                    'intake_complete': complete
                },
                'confidence': 0.3,
                'warnings': [f'Intake LLM failed, fallback used: {str(e)}']
            }
