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
from langsmith import traceable
from langsmith.wrappers import wrap_openai
from backend.utils.llm_utils import llm_call_with_retry

logger = logging.getLogger('petcare.agents.intake')

import re as _re

REQUIRED_FIELDS = ['species', 'chief_complaint']
OPTIONAL_FIELDS = ['pet_name', 'breed', 'age', 'weight',
                   'timeline', 'eating_drinking', 'energy_level']


def _sanitize_for_prompt(value: str, max_len: int = 200) -> str:
    """Strip control chars and limit length to prevent prompt injection."""
    if not value:
        return ''
    cleaned = _re.sub(r'[\x00-\x1f\x7f]', ' ', str(value))
    return cleaned.strip()[:max_len]


class IntakeAgent:
    """LLM-powered adaptive symptom intake agent."""

    def __init__(self):
        self.agent_name = 'intake'

    _SPECIES_WORDS = {
        # English
        'dog', 'cat', 'bird', 'rabbit', 'hamster', 'reptile', 'fish',
        'parrot', 'puppy', 'kitten', 'bunny', 'turtle', 'snake', 'lizard',
        'guinea pig', 'gerbil', 'ferret', 'pet', 'animal',
        'chicken', 'rooster', 'hen', 'duck', 'goose', 'turkey', 'pigeon',
        'horse', 'pony', 'goat', 'sheep', 'pig', 'cow', 'calf',
        'hedgehog', 'chinchilla', 'rat', 'mouse', 'frog', 'toad',
        'cockatiel', 'budgie', 'canary', 'macaw', 'cockatoo', 'finch',
        # French
        'chien', 'chienne', 'chiot', 'chat', 'chatte', 'chaton',
        'oiseau', 'lapin', 'poisson', 'cheval', 'poney', 'chèvre',
        'mouton', 'cochon', 'vache', 'veau', 'canard', 'oie', 'dinde',
        'tortue', 'serpent', 'lézard', 'perroquet', 'hamster', 'furet',
        'souris', 'grenouille', 'hérisson', 'animal de compagnie',
        # Spanish
        'perro', 'perra', 'perrito', 'cachorro', 'gato', 'gata', 'gatito',
        'pájaro', 'ave', 'conejo', 'pez', 'caballo', 'yegua', 'cabra',
        'oveja', 'cerdo', 'vaca', 'ternero', 'pato', 'ganso', 'pavo',
        'tortuga', 'serpiente', 'lagarto', 'loro', 'hámster', 'hurón',
        'ratón', 'rana', 'erizo', 'mascota',
        # Hindi
        'कुत्ता', 'कुत्ती', 'पिल्ला', 'बिल्ली', 'बिल्ला', 'बिल्ली का बच्चा',
        'पक्षी', 'चिड़िया', 'खरगोश', 'मछली', 'घोड़ा', 'घोड़ी', 'टट्टू',
        'बकरी', 'बकरा', 'भेड़', 'सूअर', 'गाय', 'बछड़ा', 'बत्तख', 'हंस',
        'कछुआ', 'सांप', 'छिपकली', 'तोता', 'चूहा', 'मेंढक', 'मुर्गी',
        'मुर्गा', 'जानवर', 'पालतू', 'पालतू जानवर',
        # Urdu
        'کتا', 'کتی', 'بلی', 'بلا', 'پرندہ', 'خرگوش', 'مچھلی',
        'گھوڑا', 'گھوڑی', 'بکری', 'بکرا', 'بھیڑ', 'سور', 'گائے',
        'بچھڑا', 'بطخ', 'کچھوا', 'سانپ', 'چھپکلی', 'طوطا', 'چوہا',
        'مینڈک', 'مرغی', 'مرغا', 'جانور', 'پالتو', 'پالتو جانور',
        # Arabic
        'كلب', 'قطة', 'قط', 'طائر', 'عصفور', 'أرنب', 'سمكة', 'حصان',
        'فرس', 'ماعز', 'خروف', 'غنم', 'خنزير', 'بقرة', 'عجل', 'بطة',
        'أوزة', 'سلحفاة', 'ثعبان', 'سحلية', 'ببغاء', 'هامستر',
        'فأر', 'ضفدع', 'دجاجة', 'ديك', 'حيوان', 'حيوان أليف',
        # Chinese
        '狗', '犬', '小狗', '猫', '小猫', '猫咪', '鸟', '兔子', '兔',
        '鱼', '马', '羊', '猪', '牛', '鸭', '鹅', '龟', '蛇', '蜥蜴',
        '鹦鹉', '仓鼠', '雪貂', '鼠', '青蛙', '鸡', '公鸡', '宠物', '动物',
    }
    # ── LLM09-9A: Plausibility dictionary ────────────────────────────────────
    # Maps lowercase species names to symptom substrings that are anatomically
    # impossible for that species.  Used by _check_plausibility() to catch
    # nonsense inputs before the LLM pipeline silently accepts them.
    #
    # Design notes:
    #   • Kept deliberately narrow — we only flag clear anatomical
    #     impossibilities, never ambiguous edge cases.  A false positive
    #     (wrongly blocking a real symptom) is more harmful than a false
    #     negative here, because it would interrupt a legitimate triage.
    #   • The LLM system prompt (rule 10) is also updated to flag impossible
    #     symptoms, but LLMs can silently accept nonsense — this deterministic
    #     layer is the guaranteed fallback.
    #   • Patterns are lowercase substrings matched against the lowercased
    #     chief_complaint.  Whole-word matching is not required because the
    #     false-positive risk for partial matches is negligible (e.g. "growling"
    #     contains "grow", but "growling" is specific enough).
    _SPECIES_IMPOSSIBLE_SYMPTOMS: dict[str, list[str]] = {
        # Fish have no lungs, no vocal cords, and no legs.
        'fish': [
            'barking', 'bark', 'growling', 'growl', 'meowing', 'meow',
            'broken leg', 'broken arm', 'limping', 'limp',
            'sneezing', 'sneeze', 'coughing', 'cough',
            'fur loss', 'hair loss', 'scratching fur',
        ],
        # Snakes have no limbs and no external ears.
        'snake': [
            'barking', 'bark', 'meowing', 'meow', 'limping', 'limp',
            'broken leg', 'paw', 'fur loss', 'hair loss',
        ],
        # Turtles / tortoises have no fur or hair.
        'turtle':   ['barking', 'bark', 'meowing', 'meow', 'fur loss', 'hair loss'],
        'tortoise': ['barking', 'bark', 'meowing', 'meow', 'fur loss', 'hair loss'],
        # Frogs and toads have no fur and no barking/meowing capability.
        'frog':     ['barking', 'bark', 'meowing', 'meow', 'fur loss', 'hair loss', 'broken leg'],
        'toad':     ['barking', 'bark', 'meowing', 'meow', 'fur loss', 'hair loss', 'broken leg'],
    }

    _NOISE_PHRASES = {
        # English
        'i have a', 'i got a', 'my pet is', 'we have a', 'it is a',
        'she is a', 'he is a', 'its a', "it's a",
        # French
        "j'ai un", "j'ai une", 'mon animal est', 'notre animal est',
        "c'est un", "c'est une",
        # Spanish
        'tengo un', 'tengo una', 'mi mascota es', 'es un', 'es una',
        # Hindi
        'मेरे पास', 'मेरा पालतू', 'हमारे पास', 'यह है', 'यह एक',
        'मेरे पास एक', 'मेरा', 'मेरी', 'हमारा', 'हमारी', 'है',
        # Urdu
        'میرے پاس', 'میرا پالتو', 'ہمارے پاس', 'یہ ہے', 'یہ ایک',
        'میرا', 'میری', 'ہمارا', 'ہماری',
        # Arabic
        'عندي', 'لدي', 'حيواني هو', 'هو', 'هي',
        # Chinese
        '我有一只', '我有一个', '我家的', '这是一只', '我的宠物是',
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

    @classmethod
    def _check_plausibility(cls, species: str, complaint: str) -> tuple[bool, str]:
        """
        Check whether the symptom description is anatomically plausible for
        the stated species.

        Returns:
            (is_plausible: bool, matched_term: str)
            is_plausible=False  → an impossible symptom was found.
            matched_term        → the exact impossible substring detected
                                  (used for logging and the follow-up question).

        This is the deterministic half of the LLM09-9A fix.  The LLM system
        prompt (rule 10) is the first line of defence, but LLMs can silently
        accept biologically nonsensical input.  This method is the guaranteed
        fallback: it runs on every call to process() after the complaint is
        extracted and before intake_complete is allowed to be True.

        Only entries in _SPECIES_IMPOSSIBLE_SYMPTOMS are checked.  Unknown
        species (e.g. 'chinchilla') simply return (True, '') — better to let
        an unusual case through than to block a legitimate triage.
        """
        if not species or not complaint:
            return True, ''
        c = complaint.lower()
        for term in cls._SPECIES_IMPOSSIBLE_SYMPTOMS.get(species.lower().strip(), []):
            if term in c:
                return False, term
        return True, ''

    # Localized fallback questions per language
    _FALLBACK_ASK_SPECIES = {
        'en': 'What type of pet do you have? (dog, cat, or other)',
        'fr': 'Quel type d\'animal avez-vous ? (chien, chat ou autre)',
        'es': '¿Qué tipo de mascota tiene? (perro, gato u otro)',
        'zh': '您的宠物是什么类型？（狗、猫或其他）',
        'ar': 'ما نوع حيوانك الأليف؟ (كلب، قطة، أو غير ذلك)',
        'hi': 'आपका पालतू जानवर किस प्रकार का है? (कुत्ता, बिल्ली, या अन्य)',
        'ur': 'آپ کا پالتو جانور کس قسم کا ہے؟ (کتا، بلی، یا کوئی اور)',
    }
    _FALLBACK_ASK_SYMPTOMS = {
        'en': 'Thanks! What symptoms or concerns are you noticing with your pet?',
        'fr': 'Merci ! Quels symptômes ou inquiétudes remarquez-vous chez votre animal ?',
        'es': '¡Gracias! ¿Qué síntomas o preocupaciones nota en su mascota?',
        'zh': '谢谢！您注意到宠物有什么症状或问题？',
        'ar': 'شكراً! ما هي الأعراض أو المخاوف التي تلاحظها على حيوانك الأليف؟',
        'hi': 'धन्यवाद! आप अपने पालतू जानवर में कौन से लक्षण या चिंताएँ देख रहे हैं?',
        'ur': 'شکریہ! آپ اپنے پالتو جانور میں کیا علامات یا تشویش دیکھ رہے ہیں؟',
    }

    def _fallback_response(self, session: dict, user_message: str, known_species: str, known_complaint: str) -> dict:
        """Return a graceful fallback when LLM fails or returns empty/invalid JSON."""
        final_species = known_species or session.get('pet_profile', {}).get('species', '')
        candidate = known_complaint or session.get('symptoms', {}).get('chief_complaint', '') or user_message

        if self._is_real_complaint(candidate, final_species):
            final_complaint = candidate
            session.setdefault('symptoms', {})['chief_complaint'] = final_complaint
        else:
            final_complaint = ''

        complete = bool(final_species and final_complaint)
        lang_code = session.get('language', 'en')
        fq = []
        if not final_species:
            fq = [self._FALLBACK_ASK_SPECIES.get(lang_code, self._FALLBACK_ASK_SPECIES['en'])]
        elif not final_complaint:
            fq = [self._FALLBACK_ASK_SYMPTOMS.get(lang_code, self._FALLBACK_ASK_SYMPTOMS['en'])]

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
            'confidence': 0.5,
            'warnings': ['Used fallback extraction due to LLM response issue']
        }

    def process(self, session: dict, user_message: str) -> dict:
        """
        Extract structured intake data from the owner message via LLM.
        Sets intake_complete=True as soon as species + chief_complaint
        are both known. Never diagnoses or names conditions.
        Falls back to simple extraction on LLM failure.
        """
        client = wrap_openai(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
        lang_code = session.get('language', 'en')
        lang_names = {
            'en': 'English', 'fr': 'French', 'zh': 'Chinese (Mandarin)',
            'ar': 'Arabic', 'es': 'Spanish', 'hi': 'Hindi', 'ur': 'Urdu'
        }
        lang_name = lang_names.get(lang_code, 'English')

        known_species = _sanitize_for_prompt(
            session.get('pet_profile', {}).get('species', ''), max_len=50
        )
        known_complaint = _sanitize_for_prompt(
            session.get('symptoms', {}).get('chief_complaint', ''), max_len=200
        )

        system_prompt = f"""You are a warm, empathetic veterinary receptionist conducting a conversational symptom intake. Your goal is to gather enough information to help the clinic prepare — not to interrogate the owner.

HARD RULES — never violate:
1. NEVER name a disease, condition, or diagnosis
2. NEVER suggest medications or dosages
3. NEVER say "your pet has", "this sounds like", "this could be"
4. ANY animal is a valid species — dogs, cats, birds, chickens, horses, reptiles, fish, farm animals, exotic pets, etc.
5. Do NOT comment on urgency at all
6. Respond in {lang_name}. ALL text values in the JSON (follow_up_questions, chief_complaint descriptions) MUST be in {lang_name}. JSON keys must stay in English.
7. Respond ONLY with valid JSON. No markdown fences. No text outside the JSON.
8. NEVER GUESS the species. Only record species if the owner explicitly mentions an animal type. Do NOT infer from greetings or vague text.
9. If the message has no pet or health content (greetings, gibberish), set all fields empty, intake_complete to false, ask what type of pet they have.
10. PLAUSIBILITY CHECK — if species+complaint are BOTH known and the symptom is anatomically impossible (fish barking, snake limping, turtle with fur), set intake_complete=false and ask the owner to describe what they actually observed.

Already known — do NOT ask for these again:
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

INTAKE COMPLETION RULES:
- Set intake_complete=TRUE as soon as species AND a real chief_complaint are BOTH known
- chief_complaint = any health concern, symptom, or reason for visit
- "general checkup", "routine visit", "wellness check" ARE valid chief complaints
- "I have a dog" identifies species only — ask what the concern is
- Once BOTH are known: set intake_complete=true, follow_up_questions=[]
- DO NOT keep asking for timeline, eating/drinking, or energy once intake is complete — the triage agent will gather those naturally
- If species="{known_species}" is already known, do NOT ask for it again
- If chief_complaint="{known_complaint}" is already known, do NOT ask for it again

TIMELINE / DATE ANSWERS:
- Accept ANY duration or date format the owner gives: "since Monday", "since March 1st", "about a week", "started yesterday", "for the past few days", "this morning"
- Store whatever they say verbatim in symptom_details.timeline — do NOT reject or re-ask
- A timeline answer does NOT change intake_complete unless species or complaint is still missing

CONVERSATIONAL STYLE:
- Ask ONE question at a time, naturally and warmly
- If the owner gives a partial answer, acknowledge it and ask for the ONE most important missing piece
- Never fire multiple questions in one turn
- Match the owner's language and tone — casual if they are casual, more formal if they are formal
- follow_up_questions must be a list with AT MOST ONE plain string. Never objects.
  WRONG: [{{"question": "How old?"}}]
  RIGHT: ["How old is your pet?"]

For symptom_details.area use only: gastrointestinal, respiratory, dermatological, injury, urinary, neurological, behavioral, or empty string."""

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
            raw = llm_call_with_retry(
                client,
                model='gpt-4o-mini',
                max_tokens=500,
                temperature=0.3,   # Slightly warmer → more natural phrasing, still deterministic
                messages=[{'role': 'system', 'content': system_prompt}] + history
            )
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

            if not raw:
                logger.warning('Intake LLM returned empty response, using fallback')
                return self._fallback_response(session, user_message, known_species, known_complaint)

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.warning(f'Intake LLM returned invalid JSON: {e}, raw={raw[:100]}...')
                return self._fallback_response(session, user_message, known_species, known_complaint)

            pet_profile = parsed.get('pet_profile', {})
            symptom_details = parsed.get('symptom_details', {})
            llm_complaint = parsed.get('chief_complaint', '')
            chief_complaint = llm_complaint or known_complaint
            intake_complete = bool(parsed.get('intake_complete', False))
            raw_questions = parsed.get('follow_up_questions', [])

            follow_up_questions = []
            for q in raw_questions:
                if isinstance(q, dict):
                    follow_up_questions.append(
                        q.get('question') or q.get('text') or str(q)
                    )
                elif isinstance(q, str) and q.strip():
                    follow_up_questions.append(q.strip())

            species = (pet_profile.get('species') or known_species or '').lower().strip()
            if species:
                session.setdefault('pet_profile', {})['species'] = species
                pet_profile['species'] = species

            for k, v in pet_profile.items():
                if v and k != 'species':
                    session.setdefault('pet_profile', {})[k] = v

            # Pick the best complaint: prefer LLM's if valid, else try known,
            # else try the raw user message as a last resort.
            final_species = (species or session.get('pet_profile', {}).get('species', ''))
            best_complaint = ''
            for candidate in [llm_complaint, known_complaint, user_message.strip()]:
                if candidate and self._is_real_complaint(candidate, final_species):
                    best_complaint = candidate
                    break

            if best_complaint:
                chief_complaint = best_complaint
                session.setdefault('symptoms', {})['chief_complaint'] = best_complaint
            elif chief_complaint:
                session.setdefault('symptoms', {})['chief_complaint'] = chief_complaint

            for k, v in symptom_details.items():
                if v:
                    session.setdefault('symptoms', {})[k] = v

            final_complaint = session.get('symptoms', {}).get('chief_complaint', '')

            if final_species and final_complaint and self._is_real_complaint(final_complaint, final_species):
                intake_complete = True
                follow_up_questions = []

            # ── LLM09-9A: Plausibility guard (deterministic layer) ────────────
            # The LLM was instructed via rule 10 to flag impossible symptoms,
            # but empirical testing showed it silently accepted e.g. a fish
            # barking.  This deterministic check is the guaranteed fallback:
            # if the species+complaint combination is anatomically impossible,
            # we override intake_complete and inject a clarifying question.
            #
            # We only override when intake_complete would be True — there is
            # no point adding a plausibility question if we still need the
            # species or chief_complaint.
            if intake_complete:
                plausible, impossible_term = self._check_plausibility(
                    final_species, final_complaint
                )
                if not plausible:
                    intake_complete = False
                    follow_up_questions = [
                        f"I want to make sure I understand — some of the details "
                        f"you described seem unusual for a {final_species}. Could "
                        f"you describe what you're actually observing? For example, "
                        f"any changes in movement, appearance, breathing, or eating?"
                    ]
                    logger.warning(
                        "Plausibility flag: species='%s' impossible_symptom='%s'",
                        final_species, impossible_term
                    )

            if not intake_complete and not follow_up_questions:
                if not final_species:
                    follow_up_questions = [self._FALLBACK_ASK_SPECIES.get(lang_code, self._FALLBACK_ASK_SPECIES['en'])]
                elif not final_complaint or not self._is_real_complaint(final_complaint, final_species):
                    follow_up_questions = [
                        self._FALLBACK_ASK_SYMPTOMS.get(lang_code, self._FALLBACK_ASK_SYMPTOMS['en'])
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
            lang_code = session.get('language', 'en')

    @traceable(name="intake.enrich_context", tags=["intake", "enrichment"])
    def enrich_context(self, session: dict) -> str | None:
        """
        Generate ONE contextually appropriate follow-up question after intake completes.

        Called by the orchestrator in place of the rigid timeline→eating→energy
        script. The LLM picks the single most clinically relevant question for
        the specific complaint — e.g. for a limping dog it asks about weight-bearing,
        not about appetite; for vomiting it asks about fluid intake.

        Returns the question string, or None if sufficient context already exists
        or if the case is clearly routine (no enrichment needed).
        """
        client = wrap_openai(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

        species = _sanitize_for_prompt(
            session.get('pet_profile', {}).get('species', 'pet'), max_len=50
        ) or 'pet'
        complaint = _sanitize_for_prompt(
            session.get('symptoms', {}).get('chief_complaint', ''), max_len=200
        )
        symptoms = session.get('symptoms', {})
        lang_code = session.get('language', 'en')
        lang_names = {
            'en': 'English', 'fr': 'French', 'zh': 'Chinese (Mandarin)',
            'ar': 'Arabic', 'es': 'Spanish', 'hi': 'Hindi', 'ur': 'Urdu'
        }
        lang_name = lang_names.get(lang_code, 'English')

        has_timeline = bool(symptoms.get('timeline'))
        has_eating   = bool(symptoms.get('eating_drinking'))
        has_energy   = bool(symptoms.get('energy_level'))

        # If all three context fields are already captured, nothing more to ask
        if has_timeline and has_eating and has_energy:
            return None

        known_parts = []
        if has_timeline:
            known_parts.append(f"timeline: {symptoms['timeline']}")
        if has_eating:
            known_parts.append(f"eating/drinking: {symptoms['eating_drinking']}")
        if has_energy:
            known_parts.append(f"energy/behaviour: {symptoms['energy_level']}")
        known_str = ', '.join(known_parts) if known_parts else 'none yet'

        missing = []
        if not has_timeline:
            missing.append('timeline (when symptoms started)')
        if not has_eating:
            missing.append('eating / drinking status')
        if not has_energy:
            missing.append('energy / behaviour')

        system_prompt = f"""You are a warm veterinary receptionist finishing an intake conversation.

The owner has told you their pet's main problem. You need ONE more piece of information to help the vet prepare.

Pet species : {species}
Chief complaint : {complaint}
Context already captured: {known_str}
Still missing (pick the ONE most relevant): {', '.join(missing)}

YOUR TASK:
Ask ONE warm, natural, complaint-specific question. Choose the missing field that is MOST RELEVANT to the specific complaint above.

GOOD EXAMPLES:
- Complaint "vomiting x2 days" → "Is your {species} still drinking water, or has that stopped too?"
- Complaint "limping on front left leg" → "When did you first notice the limping — did something happen, or did it come on gradually?"
- Complaint "ruffled feathers, quiet" (bird) → "Has your {species} been eating and passing droppings as usual?"
- Complaint "not eating" → "How long has your {species} been off food — and is it still drinking?"
- Complaint "lump on side" → "How long have you noticed the lump — and has it changed in size?"
- Complaint "routine checkup / wellness" → SKIP

RULES:
1. Return ONLY the plain question — no preamble, no JSON, just the question text
2. Make it feel like a natural continuation of the conversation, not a form field
3. ONE question only — never combine two questions into one turn
4. Respond in {lang_name}
5. NEVER name a disease or suggest a diagnosis
6. If the complaint is clearly a routine wellness visit with nothing to clarify, return exactly the word: SKIP"""

        try:
            question = llm_call_with_retry(
                client,
                model='gpt-4o-mini',
                max_tokens=80,
                temperature=0.4,
                messages=[{'role': 'system', 'content': system_prompt}]
            )
            if not question or question.upper() == 'SKIP' or len(question) < 5:
                return None
            return question
        except Exception as e:
            logger.warning(f'Context enrichment LLM error: {e}')
            return None
