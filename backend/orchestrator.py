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

import os
import time
import logging
import re
import requests
from datetime import datetime
from langsmith import traceable
import guardrails


# ---------------------------------------------------------------------------
# Invalid species guardrails
# ---------------------------------------------------------------------------
# Species values that must never be accepted — regardless of how they arrived
# (LLM extraction, keyword fallback, or user free-text).

# Humans described as pets — we respond with a compassionate redirect.
_INVALID_SPECIES_HUMANS = frozenset({
    # English
    'human', 'humans', 'person', 'people', 'man', 'men', 'woman', 'women',
    'boy', 'girl', 'child', 'children', 'baby', 'babies', 'infant', 'toddler',
    'teenager', 'teen', 'adult', 'elderly', 'senior', 'patient',
    'husband', 'wife', 'spouse', 'partner', 'boyfriend', 'girlfriend',
    'friend', 'neighbour', 'neighbor', 'sibling', 'brother', 'sister',
    # French
    'homme', 'femme', 'enfant', 'bébé', 'personne', 'gens', 'mari', 'épouse',
    'garçon', 'fille', 'adulte', 'bébé', 'nourrisson', 'adolescent',
    # Spanish
    'hombre', 'mujer', 'niño', 'niña', 'bebé', 'persona', 'personas',
    'marido', 'esposa', 'amigo', 'hermano', 'hermana',
    # Chinese
    '人', '男人', '女人', '孩子', '婴儿', '男孩', '女孩', '老人', '成人', '朋友',
    # Arabic
    'إنسان', 'شخص', 'رجل', 'امرأة', 'طفل', 'طفلة', 'رضيع', 'صديق',
    # Hindi
    'इंसान', 'व्यक्ति', 'आदमी', 'औरत', 'बच्चा', 'बच्ची', 'शिशु', 'दोस्त',
    # Urdu
    'انسان', 'شخص', 'مرد', 'عورت', 'بچہ', 'بچی', 'دوست',
})

# Clearly fictional creatures — we respond with a gentle redirect.
_INVALID_SPECIES_FICTIONAL = frozenset({
    'dragon', 'dragons', 'unicorn', 'unicorns', 'phoenix', 'griffin', 'griffon',
    'gryphon', 'pegasus', 'mermaid', 'vampire', 'zombie', 'werewolf', 'goblin',
    'elf', 'fairy', 'sprite', 'demon', 'angel', 'centaur', 'minotaur',
    'kraken', 'hydra', 'chimera', 'manticore', 'basilisk',
})

# Words in the current message that strongly suggest a complaint rather than
# a species name — used in the exotic species Pass 1b guard.
_COMPLAINT_WORDS = frozenset({
    'sick', 'ill', 'hurt', 'pain', 'vomit', 'vomiting', 'limp', 'limping',
    'bleeding', 'breathing', 'seizure', 'collapse', 'eating', 'drinking',
    'sleeping', 'lethargic', 'swollen', 'itching', 'scratching', 'coughing',
    'sneezing', 'diarrhea', 'constipated', 'lumps', 'bump', 'infection',
    'wound', 'injury', 'fever', 'discharge', 'sores', 'rash', 'losing',
    'gained', 'weight', 'water', 'food', 'lately', 'yesterday', 'today',
    'week', 'days', 'hours', 'morning', 'night', 'suddenly', 'gradually',
    'worse', 'better', 'same', 'normal', 'abnormal', 'unusual',
    # common short stopwords that are never species
    'not', 'no', 'yes', 'ok', 'the', 'my', 'our', 'a', 'an', 'is', 'has',
    'and', 'or', 'but', 'so', 'very', 'really', 'just', 'too', 'its',
    'hi', 'hello', 'hey', 'please', 'thank', 'thanks', 'also',
})

# ---------------------------------------------------------------------------
# Social / greeting detection — BUG-03 fix
# ---------------------------------------------------------------------------
# Patterns that identify a message as purely social (no pet/symptom content).
# Checked BEFORE calling the intake agent so we never re-ask the same question.
_SOCIAL_PATTERNS = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in [
    # English greetings & pleasantries
    r'^(hi|hey|hello|howdy|greetings|good\s+(morning|afternoon|evening|day|night))[\s!,.]*$',
    r'\bhow\s+are\s+you\b',
    r'\bhow\s+r\s+u\b',
    r'\bwhat\'?s\s+up\b',
    r'\bnice\s+to\s+(meet|chat|talk)\b',
    r'\bi\'?m\s+(fine|good|great|well|ok|okay|doing\s+(well|good|great|fine))\b',
    # Name introductions  ("Hello, this is Diana" / "My name is X" / "hi im Syed")
    r'\bmy\s+name\s+is\b',
    r'\bthis\s+is\s+[A-Za-z]+\b',
    r'\bi\s+am\s+[A-Za-z]+\b(?!.*\b(sick|ill|hurt|vomit|lethargic|bleed|pain)\b)',
    # "hi im [Name]" / "hey I'm [Name]" / "hello im [Name]" — greeting + name intro
    r'\b(hi|hey|hello|howdy)\b.{0,50}\bi\'?m\s+[A-Za-z]{2,30}\b',
    # French
    r'\b(bonjour|bonsoir|bonne\s+(nuit|journée|soirée)|salut|coucou)\b',
    r'\bcomment\s+(allez.vous|vas.tu|ça\s+va)\b',
    r'\bje\s+m\'appelle\b',
    # Spanish
    r'\b(hola|buenos\s+(días|tardes|noches)|buenas)\b',
    r'\bcómo\s+(está|estás|estáis)\b',
    r'\bme\s+llamo\b',
    # Hindi / Urdu
    r'\b(namaste|namaskar|salam|assalam|aoa|adab)\b',
    r'\bmera\s+naam\b',
    # Arabic
    r'\b(مرحبا|السلام\s+عليكم|أهلا|صباح\s+الخير|مساء\s+الخير|كيف\s+حالك)\b',
    # Chinese
    r'(你好|早上好|下午好|晚上好|您好)',
]]

# Name extraction from a greeting message
_NAME_FROM_GREETING_RE = re.compile(
    r'\b(?:my\s+name\s+is|this\s+is|i\s+am|i\'?m|je\s+m\'appelle|me\s+llamo|mera\s+naam)\s+([A-Za-zÀ-ÖØ-öø-ÿ]{2,30})\b',
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Duration / timeline pre-extraction — BUG-04 fix
# ---------------------------------------------------------------------------
# Compiled once at module load. Matches phrases like:
#   "for the last 3 days", "since yesterday", "started this morning",
#   "about a week", "for 2 weeks", "over the past few hours"
_DURATION_RE = re.compile(
    r'(?:'
    r'(?:for\s+(?:the\s+)?(?:last\s+|past\s+)?|since\s+|over\s+(?:the\s+)?(?:last\s+|past\s+)?)'
    r'(?:\d+\s+(?:day|days|week|weeks|month|months|hour|hours|year|years)'
    r'|a\s+(?:day|week|month)|few\s+(?:days|weeks|hours)|couple\s+(?:of\s+)?days'
    r'|yesterday|today|this\s+(?:morning|afternoon|evening)|monday|tuesday|wednesday'
    r'|thursday|friday|saturday|sunday)'
    r'|started\s+(?:this\s+(?:morning|afternoon|evening)|yesterday|today)'
    r'|\d+\s+(?:day|days|week|weeks|month|months|hour|hours|year|years)\s+ago'
    r'|about\s+(?:a\s+)?(?:\d+\s+)?(?:day|days|week|weeks|month|months|hour|hours)'
    r')',
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Session state constants
# ---------------------------------------------------------------------------
# Raw string literals were scattered throughout the codebase ("intake",
# "complete", "emergency", "booked"). Centralizing them here means:
#   - A typo ('compelte') is caught at import time, not at runtime
#   - IDEs can autocomplete / find-all-references
#   - Adding a new state (e.g. 'pending_payment') requires one edit here
#
# Usage:   self.session['state'] = SessionState.INTAKE
# Checks:  if state in SessionState.TERMINAL_STATES: ...
# ---------------------------------------------------------------------------
class SessionState:
    """Namespace for valid session state string constants."""
    INTAKE    = 'intake'     # Collecting pet info and symptoms
    COMPLETE  = 'complete'   # Triage + scheduling done; awaiting booking choice
    EMERGENCY = 'emergency'  # Red flag detected; owner redirected to ER
    BOOKED    = 'booked'     # Owner confirmed an appointment slot

    # States where the pipeline is finished and post-completion handler runs
    TERMINAL_STATES = frozenset({COMPLETE, EMERGENCY, BOOKED})


# ---------------------------------------------------------------------------
# Localized urgency tier labels (fixes ZH-3: English "Routine" inside
# Chinese/Arabic/Hindi/Urdu sentences).
# ---------------------------------------------------------------------------
_URGENCY_TIER_LABELS: dict[str, dict[str, str]] = {
    'Emergency': {
        'en': 'Emergency',  'fr': 'Urgence',       'es': 'Emergencia',
        'zh': '紧急',        'ar': 'طارئ',          'hi': 'आपातकाल',    'ur': 'ایمرجنسی',
    },
    'Same-day': {
        'en': 'Same-day',   'fr': 'Le jour même',  'es': 'El mismo día',
        'zh': '当天就诊',    'ar': 'في اليوم نفسه', 'hi': 'आज का',       'ur': 'آج کا',
    },
    'Soon': {
        'en': 'Soon',       'fr': 'Sous peu',      'es': 'Pronto',
        'zh': '尽快',        'ar': 'قريباً',        'hi': 'शीघ्र',      'ur': 'جلدی',
    },
    'Routine': {
        'en': 'Routine',    'fr': 'Routine',       'es': 'De rutina',
        'zh': '常规',        'ar': 'روتيني',        'hi': 'नियमित',     'ur': 'معمول',
    },
}

# Localized month names for slot date display (fixes ZH-3 English date output).
_MONTH_NAMES: dict[str, list[str]] = {
    'en': ['January','February','March','April','May','June',
           'July','August','September','October','November','December'],
    'fr': ['janvier','février','mars','avril','mai','juin',
           'juillet','août','septembre','octobre','novembre','décembre'],
    'es': ['enero','febrero','marzo','abril','mayo','junio',
           'julio','agosto','septiembre','octubre','noviembre','diciembre'],
    'zh': ['1月','2月','3月','4月','5月','6月',
           '7月','8月','9月','10月','11月','12月'],
    'ar': ['يناير','فبراير','مارس','أبريل','مايو','يونيو',
           'يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'],
    'hi': ['जनवरी','फ़रवरी','मार्च','अप्रैल','मई','जून',
           'जुलाई','अगस्त','सितंबर','अक्तूबर','नवंबर','दिसंबर'],
    'ur': ['جنوری','فروری','مارچ','اپریل','مئی','جون',
           'جولائی','اگست','ستمبر','اکتوبر','نومبر','دسمبر'],
}

# Localized day-of-week names (Mon=0 … Sun=6) for slot display.
_DAY_NAMES_DISPLAY: dict[str, list[str]] = {
    'en': ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],
    'fr': ['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche'],
    'es': ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo'],
    'zh': ['周一','周二','周三','周四','周五','周六','周日'],
    'ar': ['الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت','الأحد'],
    'hi': ['सोमवार','मंगलवार','बुधवार','गुरुवार','शुक्रवार','शनिवार','रविवार'],
    'ur': ['پیر','منگل','بدھ','جمعرات','جمعہ','ہفتہ','اتوار'],
}


def _fmt_slot_dt(dt, lang: str) -> str:
    """Return a localized, human-friendly appointment datetime string."""
    days   = _DAY_NAMES_DISPLAY.get(lang, _DAY_NAMES_DISPLAY['en'])
    months = _MONTH_NAMES.get(lang, _MONTH_NAMES['en'])
    day_name   = days[dt.weekday()]
    month_name = months[dt.month - 1]
    hour = dt.hour % 12 or 12
    minute = dt.minute
    if lang in ('zh', 'ar', 'hi', 'ur'):
        # Non-Latin scripts: use numeric format without am/pm label
        time_str = f"{dt.hour:02d}:{minute:02d}"
        return f"{day_name} {dt.day} {month_name} {time_str}"
    ampm = 'am' if dt.hour < 12 else 'pm'
    min_str = f":{minute:02d}" if minute else ""
    return f"{day_name}, {month_name} {dt.day} at {hour}{min_str} {ampm}"


# ---------------------------------------------------------------------------
# Localized UI strings for all 7 supported languages.
# These are used for all hardcoded chatbot messages (not LLM-generated).
# ---------------------------------------------------------------------------
_UI_STRINGS = {
    'en': {
        'ask_species': 'What type of pet do you have? (dog, cat, or other)',
        'ask_symptoms': 'Thanks! What symptoms or concerns are you noticing with your pet?',
        'ask_timeline': 'How long has this been going on? (e.g. a few hours, since yesterday, about a week)',
        'ask_eating': 'Is your {species} eating and drinking normally?',
        'ask_energy': 'How is your {species}\'s energy level? (normal, a bit low, or very lethargic/not moving much)',
        'need_more_info': 'I need a bit more information to help you. Could you tell me about: {missing}?',
        'connect_receptionist': 'I want to make sure your pet gets the right care. Let me connect you with our receptionist who can help complete the intake. One moment please.',
        'conflicting_info': 'Some of the information seems conflicting. Let me connect you with our receptionist to ensure we get the most accurate assessment.',
        'recommend_visit': "Thank you for sharing all of that — I want to make sure your pet gets the right care. I'd recommend a **{urgency}** visit.",
        'available_appointments': '\nI found a few appointment options that should work:',
        'while_you_wait': '\nWhile you wait, here are a few things you can do to help:',
        'dont_do': '\nA couple of things to avoid in the meantime:',
        'seek_emergency_if': '\nGo straight to an emergency clinic if you notice any of these:',
        'start_fresh': "No problem — let's start fresh!\n\nWhat type of pet do you have (dog, cat, or other)?",
        'appointment_confirmed': "Your appointment has been confirmed:\n\n  **{time}** with **{provider}**\n\nPlease bring your {species} and any relevant medical records. If symptoms worsen before the appointment, seek emergency care immediately.\n\nWould you like to start a new session for another concern? Just say **\"start over\"**.",
        'which_appointment': 'Which appointment would you like to book? Please pick one:\n\n{slots}',
        'already_booked': 'Your appointment is already booked! If you\'d like to start a new session, just say **"start over"**.',
        'would_you_book': 'Would you like to book one of these appointments?\n\n{slots}\n\nJust say which one (e.g. **"book the first one"** or **"Tuesday with Dr. Patel"**), or say **"start over"** for a new concern.',
        'triage_complete': 'Your triage is complete. You can say **"start over"** to begin a new session for a different concern.',
        'nearby_vets_offer': '\n📍 I can also help you find nearby vet clinics — just say **"find nearby vets"** if you\'d like.',
        'invalid_species_human': "I'm here to help with pet health concerns only. For human medical issues, please contact a doctor or call emergency services if needed. What type of pet do you have?",
        'invalid_species_fictional': "I can only help with real animals! It sounds like you may be describing a fictional creature. Could you tell me what type of pet you actually have? (dog, cat, rabbit, hamster, axolotl — any real animal works!)",
        'social_redirect_no_species': "{greeting}To get started, could you tell me what type of pet you have?",
        'social_redirect_has_species': "{greeting}What symptoms or concerns are you noticing with your {species}?",
        'greeting_named': "Hi {name}! ",
        'greeting_anon': "Hi there! ",
    },
    'fr': {
        'ask_species': 'Quel type d\'animal avez-vous ? (chien, chat ou autre)',
        'ask_symptoms': 'Merci ! Quels symptômes ou inquiétudes remarquez-vous chez votre animal ?',
        'ask_timeline': 'Depuis combien de temps cela dure-t-il ? (par ex. quelques heures, depuis hier, environ une semaine)',
        'ask_eating': 'Votre {species} mange-t-il et boit-il normalement ?',
        'ask_energy': 'Comment est le niveau d\'énergie de votre {species} ? (normal, un peu bas, ou très léthargique)',
        'need_more_info': 'J\'ai besoin d\'un peu plus d\'informations pour vous aider. Pourriez-vous me parler de : {missing} ?',
        'connect_receptionist': 'Je veux m\'assurer que votre animal reçoive les bons soins. Laissez-moi vous mettre en contact avec notre réceptionniste. Un instant s\'il vous plaît.',
        'conflicting_info': 'Certaines informations semblent contradictoires. Laissez-moi vous mettre en contact avec notre réceptionniste pour assurer l\'évaluation la plus précise.',
        'recommend_visit': "Merci de m'avoir tout partagé — je veux m'assurer que votre animal reçoive les bons soins. Je recommanderais une visite **{urgency}**.",
        'available_appointments': '\nVoici quelques créneaux qui pourraient vous convenir :',
        'while_you_wait': '\nEn attendant, voici quelques choses que vous pouvez faire pour aider :',
        'dont_do': '\nQuelques choses à éviter en attendant :',
        'seek_emergency_if': '\nRendez-vous directement en urgence si vous remarquez :',
        'start_fresh': "Pas de problème — recommençons !\n\nQuel type d'animal avez-vous ? (chien, chat ou autre)",
        'appointment_confirmed': "Votre rendez-vous est confirmé :\n\n  **{time}** avec **{provider}**\n\nVeuillez apporter votre {species} et tout dossier médical pertinent. Si les symptômes s'aggravent avant le rendez-vous, consultez immédiatement un vétérinaire d'urgence.\n\nSouhaitez-vous commencer une nouvelle session ? Dites simplement **\"recommencer\"**.",
        'which_appointment': 'Quel rendez-vous souhaitez-vous réserver ?\n\n{slots}',
        'already_booked': 'Votre rendez-vous est déjà réservé ! Dites **"recommencer"** pour une nouvelle session.',
        'would_you_book': 'Souhaitez-vous réserver l\'un de ces rendez-vous ?\n\n{slots}\n\nDites simplement lequel (par ex. **"réserver le premier"** ou **"mardi avec Dr. Patel"**), ou dites **"recommencer"** pour un autre problème.',
        'triage_complete': 'Votre triage est terminé. Vous pouvez dire **"recommencer"** pour une nouvelle session.',
        'invalid_species_human': "Je suis ici pour aider avec la santé des animaux de compagnie uniquement. Pour des problèmes médicaux humains, veuillez contacter un médecin. Quel type d'animal avez-vous ?",
        'invalid_species_fictional': "Je peux uniquement aider avec des animaux réels ! Quel type d'animal avez-vous ? (chien, chat, lapin, hamster — tout animal réel fonctionne !)",
        'social_redirect_no_species': "{greeting}Pour commencer, quel type d'animal avez-vous ?",
        'social_redirect_has_species': "{greeting}Quels symptômes ou inquiétudes remarquez-vous chez votre {species} ?",
        'greeting_named': "Bonjour {name} ! ",
        'greeting_anon': "Bonjour ! ",
    },
    'es': {
        'ask_species': '¿Qué tipo de mascota tiene? (perro, gato u otro)',
        'ask_symptoms': '¡Gracias! ¿Qué síntomas o preocupaciones nota en su mascota?',
        'ask_timeline': '¿Cuánto tiempo lleva ocurriendo esto? (por ej. unas horas, desde ayer, aproximadamente una semana)',
        'ask_eating': '¿Su {species} está comiendo y bebiendo normalmente?',
        'ask_energy': '¿Cómo está el nivel de energía de su {species}? (normal, un poco bajo, o muy aletargado)',
        'need_more_info': 'Necesito un poco más de información para ayudarle. ¿Podría contarme sobre: {missing}?',
        'connect_receptionist': 'Quiero asegurarme de que su mascota reciba la atención adecuada. Permítame conectarlo con nuestra recepcionista. Un momento por favor.',
        'conflicting_info': 'Parte de la información parece contradictoria. Permítame conectarlo con nuestra recepcionista para asegurar la evaluación más precisa.',
        'recommend_visit': 'Gracias por contarme todo eso — quiero asegurarme de que su mascota reciba la atención adecuada. Recomendaría una visita **{urgency}**.',
        'available_appointments': '\nEncontré algunos horarios disponibles que podrían funcionar:',
        'while_you_wait': '\nMientras espera, aquí hay algunas cosas que puede hacer para ayudar:',
        'dont_do': '\nAlgunas cosas que conviene evitar por ahora:',
        'seek_emergency_if': '\nAcuda directamente a urgencias si nota alguno de estos signos:',
        'start_fresh': '¡Sin problema — empecemos de nuevo!\n\n¿Qué tipo de mascota tiene? (perro, gato u otro)',
        'appointment_confirmed': 'Su cita ha sido confirmada:\n\n  **{time}** con **{provider}**\n\nPor favor traiga a su {species} y cualquier registro médico relevante. Si los síntomas empeoran antes de la cita, busque atención de emergencia inmediatamente.\n\n¿Desea iniciar una nueva sesión? Simplemente diga **"empezar de nuevo"**.',
        'which_appointment': '¿Qué cita le gustaría reservar?\n\n{slots}',
        'already_booked': '¡Su cita ya está reservada! Diga **"empezar de nuevo"** para una nueva sesión.',
        'would_you_book': '¿Le gustaría reservar una de estas citas?\n\n{slots}\n\nDiga cuál (por ej. **"reservar la primera"** o **"martes con Dr. Patel"**), o diga **"empezar de nuevo"** para otra consulta.',
        'triage_complete': 'Su triage está completo. Puede decir **"empezar de nuevo"** para una nueva sesión.',
        'invalid_species_human': "Solo puedo ayudar con problemas de salud de mascotas. Para emergencias humanas, comuníquese con un médico. ¿Qué tipo de mascota tiene?",
        'invalid_species_fictional': "¡Solo puedo ayudar con animales reales! ¿Qué tipo de mascota tiene? (perro, gato, conejo, hámster — cualquier animal real funciona)",
        'social_redirect_no_species': "{greeting}Para empezar, ¿qué tipo de mascota tiene?",
        'social_redirect_has_species': "{greeting}¿Qué síntomas o preocupaciones nota en su {species}?",
        'greeting_named': "¡Hola {name}! ",
        'greeting_anon': "¡Hola! ",
    },
    'zh': {
        'ask_species': '您的宠物是什么类型？（狗、猫或其他）',
        'ask_symptoms': '谢谢！您注意到宠物有什么症状或问题？',
        'ask_timeline': '这种情况持续多久了？（例如几个小时、从昨天开始、大约一周）',
        'ask_eating': '您的{species}吃喝正常吗？',
        'ask_energy': '您的{species}精力如何？（正常、有点低、还是非常嗜睡/不怎么动）',
        'need_more_info': '我需要更多信息来帮助您。您能告诉我关于：{missing}？',
        'connect_receptionist': '我想确保您的宠物得到正确的护理。让我为您联系我们的接待员。请稍等。',
        'conflicting_info': '部分信息似乎有矛盾。让我为您联系我们的接待员以确保最准确的评估。',
        'recommend_visit': '感谢您分享了这些信息——我想确保您的宠物得到妥善照料。建议进行 **{urgency}** 就诊。',
        'available_appointments': '\n以下是几个合适的预约时间：',
        'while_you_wait': '\n等待期间，您可以做以下几件事来帮助您的宠物：',
        'dont_do': '\n暂时需要避免的几件事：',
        'seek_emergency_if': '\n如果您注意到以下任何迹象，请立即前往急诊：',
        'start_fresh': '没问题——让我们重新开始！\n\n您的宠物是什么类型？（狗、猫或其他）',
        'appointment_confirmed': '您的预约已确认：\n\n  **{time}** 与 **{provider}**\n\n请携带您的{species}和相关医疗记录。如果症状在预约前恶化，请立即寻求紧急护理。\n\n想要开始新的会话？请说 **"重新开始"**。',
        'which_appointment': '您想预约哪个时间？\n\n{slots}',
        'already_booked': '您的预约已经预订！说 **"重新开始"** 开始新会话。',
        'would_you_book': '您想预约以下哪个时间？\n\n{slots}\n\n请说您想选哪个（如 **"预约第一个"** 或 **"周二与Patel医生"**），或说 **"重新开始"** 处理其他问题。',
        'triage_complete': '您的分诊已完成。您可以说 **"重新开始"** 开始新会话。',
        'invalid_species_human': "我只能帮助宠物健康问题。对于人类医疗问题，请联系医生。您有什么类型的宠物？",
        'invalid_species_fictional': "我只能帮助真实的动物！您有什么类型的宠物？（狗、猫、兔子、仓鼠——任何真实动物都可以！）",
        'social_redirect_no_species': "{greeting}请问您有什么类型的宠物？",
        'social_redirect_has_species': "{greeting}您注意到您的{species}有什么症状或问题吗？",
        'greeting_named': "你好，{name}！",
        'greeting_anon': "你好！",
    },
    'ar': {
        'ask_species': 'ما نوع حيوانك الأليف؟ (كلب، قطة، أو غير ذلك)',
        'ask_symptoms': 'شكراً! ما هي الأعراض أو المخاوف التي تلاحظها على حيوانك الأليف؟',
        'ask_timeline': 'منذ متى يحدث هذا؟ (مثلاً بضع ساعات، منذ الأمس، حوالي أسبوع)',
        'ask_eating': 'هل يأكل ويشرب {species} بشكل طبيعي؟',
        'ask_energy': 'كيف مستوى طاقة {species}؟ (طبيعي، منخفض قليلاً، أو خامل جداً/لا يتحرك كثيراً)',
        'need_more_info': 'أحتاج إلى مزيد من المعلومات لمساعدتك. هل يمكنك إخباري عن: {missing}؟',
        'connect_receptionist': 'أريد التأكد من أن حيوانك الأليف يحصل على الرعاية المناسبة. دعني أوصلك بموظف الاستقبال. لحظة من فضلك.',
        'conflicting_info': 'بعض المعلومات تبدو متناقضة. دعني أوصلك بموظف الاستقبال لضمان التقييم الأكثر دقة.',
        'recommend_visit': 'شكراً لمشاركتي كل هذه التفاصيل — أريد التأكد من حصول حيوانك على الرعاية المناسبة. أنصح بزيارة **{urgency}**.',
        'available_appointments': '\nوجدت بعض المواعيد المناسبة:',
        'while_you_wait': '\nأثناء الانتظار، إليك بعض الأشياء التي يمكنك فعلها للمساعدة:',
        'dont_do': '\nبعض الأشياء التي يجب تجنبها في الوقت الحالي:',
        'seek_emergency_if': '\nتوجه فوراً للطوارئ إذا لاحظت أياً من هذه العلامات:',
        'start_fresh': 'لا مشكلة — لنبدأ من جديد!\n\nما نوع حيوانك الأليف؟ (كلب، قطة، أو غير ذلك)',
        'appointment_confirmed': 'تم تأكيد موعدك:\n\n  **{time}** مع **{provider}**\n\nيرجى إحضار {species} وأي سجلات طبية ذات صلة. إذا تفاقمت الأعراض قبل الموعد، اطلب رعاية طارئة فوراً.\n\nهل تريد بدء جلسة جديدة؟ قل **"ابدأ من جديد"**.',
        'which_appointment': 'أي موعد تريد حجزه؟\n\n{slots}',
        'already_booked': 'موعدك محجوز بالفعل! قل **"ابدأ من جديد"** لجلسة جديدة.',
        'would_you_book': 'هل تريد حجز أحد هذه المواعيد؟\n\n{slots}\n\nقل أي واحد (مثلاً **"احجز الأول"** أو **"الثلاثاء مع د. باتيل"**)، أو قل **"ابدأ من جديد"** لمشكلة أخرى.',
        'triage_complete': 'اكتمل التقييم. يمكنك قول **"ابدأ من جديد"** لجلسة جديدة.',
        'invalid_species_human': "أنا هنا للمساعدة في صحة الحيوانات الأليفة فقط. للمشاكل الطبية البشرية، يرجى الاتصال بطبيب. ما نوع حيوانك الأليف؟",
        'invalid_species_fictional': "يمكنني فقط مساعدة الحيوانات الحقيقية! ما نوع حيوانك الأليف؟ (كلب، قطة، أرنب، هامستر — أي حيوان حقيقي يناسب!)",
        'social_redirect_no_species': "{greeting}للبدء، ما نوع حيوانك الأليف؟",
        'social_redirect_has_species': "{greeting}ما الأعراض أو المخاوف التي تلاحظها على {species}؟",
        'greeting_named': "مرحباً {name}! ",
        'greeting_anon': "مرحباً! ",
    },
    'hi': {
        'ask_species': 'आपका पालतू जानवर किस प्रकार का है? (कुत्ता, बिल्ली, या अन्य)',
        'ask_symptoms': 'धन्यवाद! आप अपने पालतू जानवर में कौन से लक्षण या चिंताएँ देख रहे हैं?',
        'ask_timeline': 'यह कब से हो रहा है? (जैसे कुछ घंटे, कल से, लगभग एक हफ्ता)',
        'ask_eating': 'क्या आपका {species} सामान्य रूप से खा-पी रहा है?',
        'ask_energy': 'आपके {species} का ऊर्जा स्तर कैसा है? (सामान्य, थोड़ा कम, या बहुत सुस्त/ज़्यादा नहीं हिलता)',
        'need_more_info': 'आपकी मदद के लिए मुझे थोड़ी और जानकारी चाहिए। क्या आप बता सकते हैं: {missing}?',
        'connect_receptionist': 'मैं यह सुनिश्चित करना चाहता हूँ कि आपके पालतू जानवर को सही देखभाल मिले। मुझे आपको हमारे रिसेप्शनिस्ट से जोड़ने दें। कृपया एक क्षण रुकें।',
        'conflicting_info': 'कुछ जानकारी विरोधाभासी लग रही है। सबसे सटीक मूल्यांकन के लिए मुझे आपको रिसेप्शनिस्ट से जोड़ने दें।',
        'recommend_visit': 'यह सब बताने के लिए शुक्रिया — मैं चाहता हूँ कि आपके पालतू जानवर को सही देखभाल मिले। मैं **{urgency}** विजिट की सलाह दूँगा।',
        'available_appointments': '\nमुझे आपके लिए कुछ अच्छे अपॉइंटमेंट मिले:',
        'while_you_wait': '\nइंतज़ार के दौरान आप ये कर सकते हैं:',
        'dont_do': '\nफिलहाल इन चीज़ों से बचें:',
        'seek_emergency_if': '\nइनमें से कोई भी लक्षण दिखे तो तुरंत आपातकालीन देखभाल लें:',
        'start_fresh': 'कोई बात नहीं — चलिए नए सिरे से शुरू करते हैं!\n\nआपका पालतू जानवर किस प्रकार का है? (कुत्ता, बिल्ली, या अन्य)',
        'appointment_confirmed': 'आपकी अपॉइंटमेंट की पुष्टि हो गई है:\n\n  **{time}** **{provider}** के साथ\n\nकृपया अपने {species} और किसी भी प्रासंगिक मेडिकल रिकॉर्ड को लाएँ। यदि अपॉइंटमेंट से पहले लक्षण बिगड़ जाएँ, तो तुरंत आपातकालीन देखभाल लें।\n\nक्या आप नया सत्र शुरू करना चाहते हैं? बस **"फिर से शुरू करें"** कहें।',
        'which_appointment': 'आप कौन सी अपॉइंटमेंट बुक करना चाहेंगे?\n\n{slots}',
        'already_booked': 'आपकी अपॉइंटमेंट पहले से बुक है! **"फिर से शुरू करें"** कहें नए सत्र के लिए।',
        'would_you_book': 'क्या आप इनमें से कोई अपॉइंटमेंट बुक करना चाहेंगे?\n\n{slots}\n\nबस बताएँ कौन सी (जैसे **"पहली बुक करें"** या **"मंगलवार Dr. Patel के साथ"**), या **"फिर से शुरू करें"** कहें अन्य समस्या के लिए।',
        'triage_complete': 'आपका ट्राइएज पूरा हो गया है। आप **"फिर से शुरू करें"** कह सकते हैं नए सत्र के लिए।',
        'invalid_species_human': "मैं केवल पालतू जानवरों की स्वास्थ्य समस्याओं में मदद कर सकता हूँ। मानव चिकित्सा समस्याओं के लिए कृपया एक डॉक्टर से संपर्क करें। आपका पालतू जानवर किस प्रकार का है?",
        'invalid_species_fictional': "मैं केवल वास्तविक जानवरों की मदद कर सकता हूँ! आपका पालतू जानवर किस प्रकार का है? (कुत्ता, बिल्ली, खरगोश, हैम्स्टर — कोई भी वास्तविक जानवर चलेगा!)",
        'social_redirect_no_species': "{greeting}शुरू करने के लिए, आपका पालतू जानवर किस प्रकार का है?",
        'social_redirect_has_species': "{greeting}आप अपने {species} में कौन से लक्षण या चिंताएँ देख रहे हैं?",
        'greeting_named': "नमस्ते {name}! ",
        'greeting_anon': "नमस्ते! ",
    },
    'ur': {
        'ask_species': 'آپ کا پالتو جانور کس قسم کا ہے؟ (کتا، بلی، یا کوئی اور)',
        'ask_symptoms': 'شکریہ! آپ اپنے پالتو جانور میں کیا علامات یا تشویش دیکھ رہے ہیں؟',
        'ask_timeline': 'یہ کب سے ہو رہا ہے؟ (مثلاً چند گھنٹے، کل سے، تقریباً ایک ہفتہ)',
        'ask_eating': 'کیا آپ کا {species} عام طور پر کھا پی رہا ہے؟',
        'ask_energy': 'آپ کے {species} کی توانائی کی سطح کیسی ہے؟ (نارمل، تھوڑی کم، یا بہت سست/زیادہ نہیں ہلتا)',
        'need_more_info': 'آپ کی مدد کے لیے مجھے تھوڑی اور معلومات چاہیے۔ کیا آپ بتا سکتے ہیں: {missing}؟',
        'connect_receptionist': 'میں یقینی بنانا چاہتا ہوں کہ آپ کے پالتو جانور کو صحیح دیکھ بھال ملے۔ مجھے آپ کو ہمارے ریسپشنسٹ سے جوڑنے دیں۔ ایک لمحہ۔',
        'conflicting_info': 'کچھ معلومات متضاد لگ رہی ہیں۔ سب سے درست تشخیص کے لیے مجھے آپ کو ریسپشنسٹ سے جوڑنے دیں۔',
        'recommend_visit': 'یہ سب بتانے کا شکریہ — میں چاہتا ہوں کہ آپ کے پالتو جانور کو بہترین دیکھ بھال ملے۔ میں **{urgency}** وزٹ کی سفارش کروں گا۔',
        'available_appointments': '\nآپ کے لیے چند مناسب ملاقات کے وقت ملے:',
        'while_you_wait': '\nانتظار کے دوران آپ یہ کر سکتے ہیں:',
        'dont_do': '\nابھی ان چیزوں سے گریز کریں:',
        'seek_emergency_if': '\nاگر آپ ان میں سے کوئی بھی علامت دیکھیں تو فوری ایمرجنسی کیئر لیں:',
        'start_fresh': 'کوئی بات نہیں — چلیں نئے سرے سے شروع کرتے ہیں!\n\nآپ کا پالتو جانور کس قسم کا ہے؟ (کتا، بلی، یا کوئی اور)',
        'appointment_confirmed': 'آپ کی ملاقات کی تصدیق ہو گئی ہے:\n\n  **{time}** **{provider}** کے ساتھ\n\nبراہ کرم اپنے {species} اور متعلقہ میڈیکل ریکارڈ لائیں۔ اگر ملاقات سے پہلے علامات بگڑ جائیں تو فوری ایمرجنسی کیئر لیں۔\n\nکیا آپ نیا سیشن شروع کرنا چاہتے ہیں؟ بس **"دوبارہ شروع کریں"** کہیں۔',
        'which_appointment': 'آپ کون سی ملاقات بک کرنا چاہیں گے?\n\n{slots}',
        'already_booked': 'آپ کی ملاقات پہلے سے بک ہے! **"دوبارہ شروع کریں"** کہیں نئے سیشن کے لیے۔',
        'would_you_book': 'کیا آپ ان میں سے کوئی ملاقات بک کرنا چاہیں گے?\n\n{slots}\n\nبس بتائیں کون سی (مثلاً **"پہلی بک کریں"** یا **"منگل Dr. Patel کے ساتھ"**), یا **"دوبارہ شروع کریں"** کہیں کسی اور مسئلے کے لیے۔',
        'triage_complete': 'آپ کا ٹرائیج مکمل ہو گیا ہے۔ آپ نئے سیشن کے لیے **"دوبارہ شروع کریں"** کہ سکتے ہیں۔',
        'invalid_species_human': "میں صرف پالتو جانوروں کی صحت سے متعلق مسائل میں مدد کر سکتا ہوں۔ انسانی طبی مسائل کے لیے براہ کرم ڈاکٹر سے رابطہ کریں۔ آپ کا پالتو جانور کس قسم کا ہے؟",
        'invalid_species_fictional': "میں صرف حقیقی جانوروں کی مدد کر سکتا ہوں! آپ کا پالتو جانور کس قسم کا ہے؟ (کتا، بلی، خرگوش، ہیمسٹر — کوئی بھی حقیقی جانور چلے گا!)",
        'social_redirect_no_species': "{greeting}شروع کرنے کے لیے، آپ کا پالتو جانور کس قسم کا ہے؟",
        'social_redirect_has_species': "{greeting}آپ اپنے {species} میں کیا علامات یا تشویش دیکھ رہے ہیں؟",
        'greeting_named': "السلام علیکم {name}! ",
        'greeting_anon': "السلام علیکم! ",
    },
}

# Restart keywords per language
_RESTART_KEYWORDS_I18N = {
    'en': {'start over', 'new session', 'reset', 'another pet', 'different pet', 'new concern', 'begin again', 'restart'},
    'fr': {'recommencer', 'nouvelle session', 'réinitialiser', 'autre animal', 'nouveau problème', 'start over', 'restart'},
    'es': {'empezar de nuevo', 'nueva sesión', 'reiniciar', 'otra mascota', 'nuevo problema', 'start over', 'restart'},
    'zh': {'重新开始', '新会话', '重置', '另一个宠物', '新问题', 'start over', 'restart'},
    'ar': {'ابدأ من جديد', 'جلسة جديدة', 'إعادة تعيين', 'حيوان آخر', 'مشكلة جديدة', 'start over', 'restart'},
    'hi': {'फिर से शुरू करें', 'नया सत्र', 'रीसेट', 'दूसरा जानवर', 'नई समस्या', 'start over', 'restart'},
    'ur': {'دوبارہ شروع کریں', 'نیا سیشن', 'ری سیٹ', 'دوسرا جانور', 'نیا مسئلہ', 'start over', 'restart'},
}

# Book keywords per language
_BOOK_KEYWORDS_I18N = {
    'en': {'book', 'confirm', 'schedule', 'yes', 'okay', 'ok', 'that one', 'first', 'second', 'third', '1st', '2nd', '3rd', 'sounds good', 'go ahead', 'please book'},
    'fr': {'réserver', 'confirmer', 'oui', 'd\'accord', 'ok', 'le premier', 'le deuxième', 'le troisième', 'ça me va', 'book', 'confirm', 'yes'},
    'es': {'reservar', 'confirmar', 'sí', 'de acuerdo', 'ok', 'el primero', 'el segundo', 'el tercero', 'suena bien', 'book', 'confirm', 'yes'},
    'zh': {'预约', '确认', '好的', '是', '第一个', '第二个', '第三个', '可以', 'book', 'confirm', 'yes', 'ok'},
    'ar': {'احجز', 'تأكيد', 'نعم', 'موافق', 'الأول', 'الثاني', 'الثالث', 'book', 'confirm', 'yes', 'ok'},
    'hi': {'बुक', 'पुष्टि', 'हाँ', 'ठीक है', 'पहला', 'दूसरा', 'तीसरा', 'book', 'confirm', 'yes', 'ok'},
    'ur': {'بک', 'تصدیق', 'ہاں', 'ٹھیک ہے', 'پہلا', 'دوسرا', 'تیسرا', 'book', 'confirm', 'yes', 'ok'},
}

# ---------------------------------------------------------------------------
# Guardrail response strings — pre-intake screen for edge-case inputs.
# Categories: non-pet subject, deceased pet, abuse/threats, normal behavior.
# ---------------------------------------------------------------------------
_GUARDRAIL_STRINGS = {
    'en': {
        'non_pet': "This service is specifically for **pet health concerns**. I'm not able to help with human health issues.\n\nIf you have a pet that needs attention, I'd love to help! What type of pet do you have? (dog, cat, or other)",
        'deceased_pet': "I'm truly sorry for your loss. Losing a pet is incredibly painful — they really are family. 💙\n\nIf you need support, here are some resources:\n  - **Pet Loss Support Hotline**: 1-855-PET-LOSS\n  - **ASPCA Pet Loss Hotline**: 1-877-GRIEF-10\n\nIf you'd like to discuss care for another pet, just say **\"start over\"**.",
        'abuse': "I understand you may be frustrated, but I need our conversation to stay respectful so I can help your pet.\n\nIf you have a pet health concern, I'm here to help. What type of pet do you have?",
        'normal_behavior': "What you're describing sounds like it could be **normal animal behavior** (e.g. mounting, play behavior). This isn't typically a medical concern.\n\nHowever, if you've noticed a **sudden change** in behavior or it seems excessive, it could be worth discussing with a vet. Would you like me to:\n  1. **Schedule a behavioral consultation**?\n  2. **Start over** with a different concern?\n\nJust let me know!",
    },
    'fr': {
        'non_pet': "Ce service est spécifiquement pour les **problèmes de santé des animaux de compagnie**. Je ne suis pas en mesure d'aider avec les problèmes de santé humaine.\n\nSi vous avez un animal qui a besoin d'attention, je serais ravi de vous aider ! Quel type d'animal avez-vous ? (chien, chat ou autre)",
        'deceased_pet': "Je suis vraiment désolé pour votre perte. Perdre un animal de compagnie est incroyablement douloureux — ils font vraiment partie de la famille. 💙\n\nSi vous souhaitez discuter des soins pour un autre animal, dites simplement **\"recommencer\"**.",
        'abuse': "Je comprends que vous puissiez être frustré, mais j'ai besoin que notre conversation reste respectueuse pour pouvoir aider votre animal.\n\nSi vous avez un problème de santé animale, je suis là pour aider. Quel type d'animal avez-vous ?",
        'normal_behavior': "Ce que vous décrivez semble être un **comportement animal normal** (par ex. chevauchement, jeu). Ce n'est généralement pas un problème médical.\n\nCependant, si vous avez remarqué un **changement soudain** de comportement, cela pourrait valoir la peine d'en discuter avec un vétérinaire. Souhaitez-vous :\n  1. **Planifier une consultation comportementale** ?\n  2. **Recommencer** avec une autre préoccupation ?",
    },
    'es': {
        'non_pet': "Este servicio es específicamente para **problemas de salud de mascotas**. No puedo ayudar con problemas de salud humana.\n\nSi tiene una mascota que necesita atención, ¡me encantaría ayudar! ¿Qué tipo de mascota tiene? (perro, gato u otro)",
        'deceased_pet': "Lamento mucho su pérdida. Perder una mascota es increíblemente doloroso — realmente son familia. 💙\n\nSi desea hablar sobre el cuidado de otra mascota, simplemente diga **\"empezar de nuevo\"**.",
        'abuse': "Entiendo que pueda estar frustrado, pero necesito que nuestra conversación sea respetuosa para poder ayudar a su mascota.\n\nSi tiene un problema de salud animal, estoy aquí para ayudar. ¿Qué tipo de mascota tiene?",
        'normal_behavior': "Lo que describe parece ser un **comportamiento animal normal** (por ej. monta, juego). Esto no suele ser un problema médico.\n\nSin embargo, si ha notado un **cambio repentino** en el comportamiento, podría valer la pena discutirlo con un veterinario. ¿Le gustaría:\n  1. **Programar una consulta de comportamiento**?\n  2. **Empezar de nuevo** con otra preocupación?",
    },
    'zh': {
        'non_pet': "本服务专门用于**宠物健康问题**。我无法帮助人类健康问题。\n\n如果您有需要关注的宠物，我很乐意帮忙！您的宠物是什么类型？（狗、猫或其他）",
        'deceased_pet': "对于您的损失，我深表遗憾。失去宠物是非常痛苦的——它们真的是家人。💙\n\n如果您想讨论另一只宠物的护理，请说 **\"重新开始\"**。",
        'abuse': "我理解您可能很沮丧，但我需要我们的对话保持尊重，以便能够帮助您的宠物。\n\n如果您有宠物健康问题，我在这里帮助您。您的宠物是什么类型？",
        'normal_behavior': "您描述的情况听起来可能是**正常的动物行为**（如骑跨、玩耍行为）。这通常不是医学问题。\n\n但是，如果您注意到行为有**突然变化**或似乎过度，可能值得与兽医讨论。您希望：\n  1. **安排行为咨询**？\n  2. **重新开始**处理其他问题？",
    },
    'ar': {
        'non_pet': "هذه الخدمة مخصصة تحديداً لـ**مشاكل صحة الحيوانات الأليفة**. لا أستطيع المساعدة في مشاكل صحة الإنسان.\n\nإذا كان لديك حيوان أليف يحتاج إلى رعاية، يسعدني المساعدة! ما نوع حيوانك الأليف؟ (كلب، قطة، أو غير ذلك)",
        'deceased_pet': "أنا آسف جداً لخسارتك. فقدان حيوان أليف مؤلم للغاية — إنهم حقاً جزء من العائلة. 💙\n\nإذا كنت ترغب في مناقشة رعاية حيوان آخر، قل **\"ابدأ من جديد\"**.",
        'abuse': "أفهم أنك قد تكون محبطاً، لكنني أحتاج أن تبقى محادثتنا محترمة حتى أتمكن من مساعدة حيوانك الأليف.\n\nإذا كان لديك مشكلة صحية حيوانية، أنا هنا للمساعدة. ما نوع حيوانك الأليف؟",
        'normal_behavior': "ما تصفه يبدو أنه قد يكون **سلوك حيواني طبيعي** (مثل الامتطاء، سلوك اللعب). هذا عادة ليس مشكلة طبية.\n\nومع ذلك، إذا لاحظت **تغييراً مفاجئاً** في السلوك، قد يكون من المفيد مناقشته مع طبيب بيطري. هل ترغب في:\n  1. **جدولة استشارة سلوكية**؟\n  2. **البدء من جديد** بمشكلة أخرى؟",
    },
    'hi': {
        'non_pet': "यह सेवा विशेष रूप से **पालतू जानवरों की स्वास्थ्य समस्याओं** के लिए है। मैं मानव स्वास्थ्य समस्याओं में मदद करने में असमर्थ हूँ।\n\nयदि आपके पास कोई पालतू जानवर है जिसे ध्यान देने की आवश्यकता है, तो मुझे मदद करने में खुशी होगी! आपका पालतू जानवर किस प्रकार का है? (कुत्ता, बिल्ली, या अन्य)",
        'deceased_pet': "आपके नुकसान के लिए मुझे सच में बहुत दुख है। पालतू जानवर को खोना अविश्वसनीय रूप से दर्दनाक है — वे वास्तव में परिवार हैं। 💙\n\nयदि आप किसी अन्य पालतू जानवर की देखभाल पर चर्चा करना चाहते हैं, तो बस **\"फिर से शुरू करें\"** कहें।",
        'abuse': "मैं समझता हूँ कि आप निराश हो सकते हैं, लेकिन मुझे हमारी बातचीत सम्मानजनक रखने की जरूरत है ताकि मैं आपके पालतू जानवर की मदद कर सकूँ।\n\nयदि आपको पालतू जानवर की स्वास्थ्य समस्या है, तो मैं मदद के लिए यहाँ हूँ। आपका पालतू जानवर किस प्रकार का है?",
        'normal_behavior': "आप जो वर्णन कर रहे हैं वह **सामान्य पशु व्यवहार** लगता है (जैसे माउंटिंग, खेल व्यवहार)। यह आमतौर पर चिकित्सा समस्या नहीं है।\n\nहालाँकि, यदि आपने व्यवहार में **अचानक बदलाव** देखा है, तो पशु चिकित्सक से चर्चा करना उपयोगी हो सकता है। क्या आप चाहेंगे:\n  1. **व्यवहार परामर्श शेड्यूल करें**?\n  2. **फिर से शुरू करें** किसी अन्य समस्या के साथ?",
    },
    'ur': {
        'non_pet': "یہ سروس خاص طور پر **پالتو جانوروں کی صحت کے مسائل** کے لیے ہے۔ میں انسانی صحت کے مسائل میں مدد کرنے سے قاصر ہوں۔\n\nاگر آپ کے پاس کوئی پالتو جانور ہے جسے توجہ کی ضرورت ہے، تو مجھے مدد کرنے میں خوشی ہوگی! آپ کا پالتو جانور کس قسم کا ہے؟ (کتا، بلی، یا کوئی اور)",
        'deceased_pet': "آپ کے نقصان پر مجھے واقعی بہت افسوس ہے۔ پالتو جانور کو کھونا ناقابل یقین حد تک تکلیف دہ ہے — وہ واقعی خاندان ہیں۔ 💙\n\nاگر آپ کسی اور پالتو جانور کی دیکھ بھال پر بات کرنا چاہتے ہیں، تو بس **\"دوبارہ شروع کریں\"** کہیں۔",
        'abuse': "میں سمجھتا ہوں کہ آپ مایوس ہو سکتے ہیں، لیکن مجھے ہماری بات چیت قابل احترام رکھنے کی ضرورت ہے تاکہ میں آپ کے پالتو جانور کی مدد کر سکوں۔\n\nاگر آپ کو پالتو جانور کی صحت کا مسئلہ ہے، تو میں مدد کے لیے حاضر ہوں۔ آپ کا پالتو جانور کس قسم کا ہے؟",
        'normal_behavior': "آپ جو بیان کر رہے ہیں وہ **عام جانوروں کا رویہ** لگتا ہے (جیسے ماؤنٹنگ، کھیل کا رویہ)۔ یہ عام طور پر طبی مسئلہ نہیں ہے۔\n\nتاہم، اگر آپ نے رویے میں **اچانک تبدیلی** دیکھی ہے، تو ویٹرنری ڈاکٹر سے بات کرنا فائدہ مند ہو سکتا ہے۔ کیا آپ چاہیں گے:\n  1. **رویے کی مشاورت شیڈول کریں**?\n  2. **دوبارہ شروع کریں** کسی اور مسئلے کے ساتھ?",
    },
}

# Map guardrail categories → _GUARDRAIL_STRINGS response keys
_GUARDRAIL_CATEGORY_MAP = {
    'prompt_injection':  'prompt_injection',
    'data_extraction':   'prompt_injection',
    'violence_weapons':  'violence',
    'sexual_explicit':   'inappropriate',
    'human_as_pet':      'human_as_pet',
    'substance_abuse':   'inappropriate',
    'abuse_harassment':  'abuse',
    'trolling_offtopic': 'offtopic',
}

# Additional response strings for new guardrail categories (injected per language)
for _lang_code, _extra in {
    'en': {
        'prompt_injection': "I'm PetCare's triage assistant, built solely for pet health questions. I can't change my role or share system details.\n\nIf you have a pet health concern, I'm here to help! What type of pet do you have?",
        'violence': "I'm not able to help with that topic. If you or someone you know is in crisis:\n  - **Crisis Text Line**: Text HOME to 741741\n  - **988 Suicide & Crisis Lifeline**: Call or text 988\n  - **Emergency**: Call 911\n\nIf you have a pet health concern, I'm here to help. What type of pet do you have?",
        'inappropriate': "This service is strictly for **pet health concerns**. I can't engage with inappropriate or off-topic content.\n\nIf you have a pet that needs attention, I'd love to help! What type of pet do you have? (dog, cat, or other)",
        'human_as_pet': "I can only assist with **actual animal companions** (dogs, cats, and other pets). I can't help with requests involving humans as pets.\n\nIf you have a pet health concern, I'm here to help! What type of pet do you have?",
        'offtopic': "I'm specifically designed for **pet health triage and booking**. I can't help with other topics.\n\nIf you have a pet that needs attention, I'd love to help! What type of pet do you have? (dog, cat, or other)",
        'non_illness_scope': "This tool is focused on **pet health symptoms and triage** — I'm not able to help with general pet care questions like feeding, training, or grooming.\n\nFor those questions, your veterinarian or a pet care resource would be a better fit.\n\nIf your pet is showing any **health symptoms or concerns**, I'm here to help. What's going on with your pet?",
    },
    'fr': {
        'prompt_injection': "Je suis l'assistant de triage PetCare, conçu uniquement pour les questions de santé animale. Je ne peux pas changer mon rôle ni partager les détails du système.\n\nSi vous avez un problème de santé animale, je suis là pour aider. Quel type d'animal avez-vous ?",
        'violence': "Je ne peux pas aider avec ce sujet. Si vous ou quelqu'un que vous connaissez est en crise, veuillez contacter les services d'urgence.\n\nSi vous avez un problème de santé animale, je suis là pour aider. Quel type d'animal avez-vous ?",
        'inappropriate': "Ce service est strictement pour les **problèmes de santé des animaux**. Je ne peux pas traiter de contenu inapproprié.\n\nSi vous avez un animal qui a besoin d'attention, je serais ravi de vous aider ! Quel type d'animal avez-vous ?",
        'human_as_pet': "Je ne peux aider qu'avec de **vrais animaux de compagnie**. Je ne peux pas traiter les demandes impliquant des humains comme animaux.\n\nSi vous avez un problème de santé animale, je suis là pour aider. Quel type d'animal avez-vous ?",
        'offtopic': "Je suis conçu pour le **triage de santé animale et la prise de rendez-vous**. Je ne peux pas aider avec d'autres sujets.\n\nSi vous avez un animal qui a besoin d'attention, je serais ravi de vous aider !",
        'non_illness_scope': "Cet outil est dédié aux **symptômes et au triage de santé animale** — je ne peux pas aider avec les questions générales sur les soins des animaux (alimentation, dressage, toilettage).\n\nPour ces questions, votre vétérinaire ou une ressource sur les soins aux animaux serait mieux adaptée.\n\nSi votre animal présente des **symptômes ou des problèmes de santé**, je suis là pour aider. Qu'est-ce qui se passe avec votre animal ?",
    },
    'es': {
        'prompt_injection': "Soy el asistente de triaje de PetCare, diseñado únicamente para preguntas de salud animal. No puedo cambiar mi rol ni compartir detalles del sistema.\n\nSi tiene un problema de salud animal, estoy aquí para ayudar. ¿Qué tipo de mascota tiene?",
        'violence': "No puedo ayudar con ese tema. Si usted o alguien que conoce está en crisis, contacte los servicios de emergencia.\n\nSi tiene un problema de salud animal, estoy aquí para ayudar. ¿Qué tipo de mascota tiene?",
        'inappropriate': "Este servicio es estrictamente para **problemas de salud de mascotas**. No puedo abordar contenido inapropiado.\n\nSi tiene una mascota que necesita atención, ¡me encantaría ayudar! ¿Qué tipo de mascota tiene?",
        'human_as_pet': "Solo puedo ayudar con **animales de compañía reales**. No puedo procesar solicitudes que involucren humanos como mascotas.\n\nSi tiene un problema de salud animal, estoy aquí para ayudar. ¿Qué tipo de mascota tiene?",
        'offtopic': "Estoy diseñado para el **triaje de salud animal y reservas**. No puedo ayudar con otros temas.\n\nSi tiene una mascota, ¡me encantaría ayudar! ¿Qué tipo de mascota tiene?",
        'non_illness_scope': "Esta herramienta está enfocada en **síntomas de salud y triage veterinario** — no puedo ayudar con preguntas generales sobre cuidado de mascotas como alimentación, entrenamiento o aseo.\n\nPara esas preguntas, su veterinario o un recurso de cuidado de mascotas sería más adecuado.\n\nSi su mascota presenta **síntomas de salud**, estoy aquí para ayudar. ¿Qué le pasa a su mascota?",
    },
    'zh': {
        'prompt_injection': "我是PetCare的分诊助手，专门为宠物健康问题而设计。我无法更改角色或分享系统详情。\n\n如果您有宠物健康问题，我在这里帮助您。您的宠物是什么类型？",
        'violence': "我无法处理这个话题。如果您或您认识的人正处于危机中，请联系紧急服务。\n\n如果您有宠物健康问题，我在这里帮助您。您的宠物是什么类型？",
        'inappropriate': "本服务严格用于**宠物健康问题**。我无法处理不当内容。\n\n如果您有需要关注的宠物，我很乐意帮忙！您的宠物是什么类型？",
        'human_as_pet': "我只能帮助**真正的宠物**（狗、猫等）。我无法处理将人类当作宠物的请求。\n\n如果您有宠物健康问题，我在这里帮助您。",
        'offtopic': "我专门为**宠物健康分诊和预约**而设计。我无法帮助其他话题。\n\n如果您有宠物，我很乐意帮忙！",
        'non_illness_scope': "本工具专注于**宠物健康症状和分诊** — 我无法帮助解答一般宠物护理问题，如喂食、训练或美容。\n\n对于这些问题，建议您咨询兽医或宠物护理资源。\n\n如果您的宠物有**健康症状**，我在这里帮助您。您的宠物怎么了？",
    },
    'ar': {
        'prompt_injection': "أنا مساعد فرز PetCare، مصمم فقط لأسئلة صحة الحيوانات الأليفة. لا أستطيع تغيير دوري أو مشاركة تفاصيل النظام.\n\nإذا كان لديك مشكلة صحية حيوانية، أنا هنا للمساعدة. ما نوع حيوانك الأليف؟",
        'violence': "لا أستطيع المساعدة في هذا الموضوع. إذا كنت أنت أو شخص تعرفه في أزمة، يرجى الاتصال بخدمات الطوارئ.\n\nإذا كان لديك مشكلة صحية حيوانية، أنا هنا للمساعدة. ما نوع حيوانك الأليف؟",
        'inappropriate': "هذه الخدمة مخصصة حصرياً لـ**مشاكل صحة الحيوانات الأليفة**. لا أستطيع التعامل مع المحتوى غير اللائق.\n\nإذا كان لديك حيوان أليف يحتاج إلى رعاية، يسعدني المساعدة!",
        'human_as_pet': "يمكنني فقط المساعدة مع **الحيوانات الأليفة الحقيقية**. لا أستطيع معالجة طلبات تتعلق بالبشر كحيوانات أليفة.\n\nإذا كان لديك مشكلة صحية حيوانية، أنا هنا للمساعدة.",
        'offtopic': "أنا مصمم لـ**فرز صحة الحيوانات والحجز**. لا أستطيع المساعدة في مواضيع أخرى.\n\nإذا كان لديك حيوان أليف، يسعدني المساعدة!",
        'non_illness_scope': "هذه الأداة تركز على **أعراض صحة الحيوانات الأليفة والفرز** — لا أستطيع المساعدة في أسئلة الرعاية العامة كالتغذية أو التدريب أو العناية.\n\nلهذه الأسئلة، طبيبك البيطري أو مصدر رعاية الحيوانات سيكون أكثر ملاءمة.\n\nإذا كان حيوانك يظهر **أعراضاً صحية**، أنا هنا للمساعدة. ما الذي يحدث مع حيوانك؟",
    },
    'hi': {
        'prompt_injection': "मैं PetCare का ट्राइएज सहायक हूँ, केवल पालतू स्वास्थ्य प्रश्नों के लिए बनाया गया। मैं अपनी भूमिका बदल नहीं सकता या सिस्टम विवरण साझा नहीं कर सकता।\n\nयदि आपको पालतू स्वास्थ्य समस्या है, तो मैं मदद के लिए यहाँ हूँ। आपका पालतू जानवर किस प्रकार का है?",
        'violence': "मैं इस विषय में मदद नहीं कर सकता। यदि आप या कोई जानने वाला संकट में है, कृपया आपातकालीन सेवाओं से संपर्क करें।\n\nयदि आपको पालतू स्वास्थ्य समस्या है, तो मैं मदद के लिए यहाँ हूँ।",
        'inappropriate': "यह सेवा विशेष रूप से **पालतू स्वास्थ्य समस्याओं** के लिए है। मैं अनुचित सामग्री पर काम नहीं कर सकता।\n\nयदि आपके पालतू जानवर को ध्यान देने की आवश्यकता है, तो मुझे मदद करने में खुशी होगी!",
        'human_as_pet': "मैं केवल **वास्तविक पालतू जानवरों** की मदद कर सकता हूँ। मैं इंसानों को पालतू जानवर के रूप में संबंधित अनुरोधों में मदद नहीं कर सकता।\n\nयदि आपको पालतू स्वास्थ्य समस्या है, तो मैं यहाँ हूँ।",
        'offtopic': "मैं **पालतू स्वास्थ्य ट्राइएज और बुकिंग** के लिए बनाया गया हूँ। मैं अन्य विषयों में मदद नहीं कर सकता।\n\nयदि आपके पालतू जानवर को ध्यान देने की आवश्यकता है, तो मुझे मदद करने में खुशी होगी!",
        'non_illness_scope': "यह उपकरण **पालतू स्वास्थ्य लक्षणों और ट्राइएज** पर केंद्रित है — मैं खान-पान, प्रशिक्षण, या सौंदर्य जैसी सामान्य देखभाल प्रश्नों में मदद नहीं कर सकता।\n\nइन प्रश्नों के लिए, आपका पशुचिकित्सक या पालतू देखभाल संसाधन अधिक उपयुक्त होगा।\n\nयदि आपके पालतू जानवर में **स्वास्थ्य लक्षण** हैं, तो मैं मदद के लिए यहाँ हूँ। आपके पालतू को क्या हो रहा है?",
    },
    'ur': {
        'prompt_injection': "میں PetCare کا ٹرائیج اسسٹنٹ ہوں، صرف پالتو جانوروں کی صحت کے سوالات کے لیے بنایا گیا۔ میں اپنا کردار تبدیل نہیں کر سکتا یا سسٹم کی تفصیلات شیئر نہیں کر سکتا۔\n\nاگر آپ کو پالتو جانور کی صحت کا مسئلہ ہے، تو میں مدد کے لیے حاضر ہوں۔",
        'violence': "میں اس موضوع میں مدد نہیں کر سکتا۔ اگر آپ یا کوئی جاننے والا بحران میں ہے، براہ کرم ایمرجنسی سروسز سے رابطہ کریں۔\n\nاگر آپ کو پالتو جانور کی صحت کا مسئلہ ہے، تو میں مدد کے لیے حاضر ہوں۔",
        'inappropriate': "یہ سروس خاص طور پر **پالتو جانوروں کی صحت کے مسائل** کے لیے ہے۔ میں نامناسب مواد پر کام کرنے سے قاصر ہوں۔\n\nاگر آپ کے پالتو جانور کو توجہ کی ضرورت ہے، تو مجھے مدد کرنے میں خوشی ہوگی!",
        'human_as_pet': "میں صرف **اصلی پالتو جانوروں** کی مدد کر سکتا ہوں۔ میں انسانوں کو پالتو جانور کے طور پر متعلقہ درخواستوں میں مدد نہیں کر سکتا۔\n\nاگر آپ کو پالتو جانور کی صحت کا مسئلہ ہے، تو میں حاضر ہوں۔",
        'offtopic': "میں **پالتو جانوروں کی صحت کی ٹرائیج اور بکنگ** کے لیے بنایا گیا ہوں۔ میں دوسرے موضوعات میں مدد نہیں کر سکتا۔\n\nاگر آپ کے پالتو جانور کو توجہ کی ضرورت ہے، تو مجھے مدد میں خوشی ہوگی!",
        'non_illness_scope': "یہ ٹول **پالتو جانوروں کی صحت کی علامات اور ٹرائیج** پر مرکوز ہے — میں خوراک، تربیت، یا گرومنگ جیسے عمومی نگہداشت کے سوالات میں مدد نہیں کر سکتا۔\n\nان سوالات کے لیے، آپ کا ویٹرنری ڈاکٹر یا پالتو جانوروں کی دیکھ بھال کا ذریعہ بہتر موزوں ہوگا۔\n\nاگر آپ کے پالتو جانور میں **صحت کی علامات** ہیں، تو میں مدد کے لیے حاضر ہوں۔ آپ کے پالتو جانور کو کیا ہو رہا ہے؟",
    },
}.items():
    _GUARDRAIL_STRINGS.setdefault(_lang_code, {}).update(_extra)


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

        # Localized UI strings for the session language
        lang = session.get('language', 'en')
        self._strings = _UI_STRINGS.get(lang, _UI_STRINGS['en'])
        self._restart_kw = _RESTART_KEYWORDS_I18N.get(lang, _RESTART_KEYWORDS_I18N['en'])
        self._book_kw = _BOOK_KEYWORDS_I18N.get(lang, _BOOK_KEYWORDS_I18N['en'])

    def _t(self, key: str, **kwargs) -> str:
        """Get a localized string, with optional format kwargs."""
        template = self._strings.get(key, _UI_STRINGS['en'].get(key, ''))
        if kwargs:
            return template.format(**kwargs)
        return template

    # ------------------------------------------------------------------
    # BUG-03: Social / greeting detection helpers
    # ------------------------------------------------------------------
    # Keywords that MUST be absent for a message to be purely social.
    # If any of these appear the message likely has pet/symptom content.
    _PET_OR_SYMPTOM_WORDS_RE = re.compile(
        r'\b(pet|dog|cat|bird|rabbit|hamster|fish|horse|pony|animal|puppy|kitten|'
        r'bunny|turtle|snake|lizard|parrot|chicken|duck|goat|cow|pig|sheep|ferret|'
        r'rat|mouse|frog|gecko|iguana|guinea\s+pig|gerbil|chinchilla|hedgehog|'
        r'sick|ill|hurt|vomit|vomiting|limp|limping|bleed|seizure|letharg|diarrhea|'
        r'cough|sneez|itch|scratch|wound|fever|pain|lump|discharge|swell|swollen|'
        r'eating|drinking|energy|symptom|concern|problem|issue|not\s+eating|not\s+well|'
        # French / Spanish / Hindi / Urdu / Arabic / Chinese key terms
        r'chien|chat|perro|gato|कुत्ता|بلی|كلب|狗|猫)\b',
        re.IGNORECASE | re.UNICODE
    )

    def _is_social_input(self, text: str) -> bool:
        """
        Return True if the message is purely a social greeting/pleasantry
        with no pet or symptom content.
        Keeps the intake loop from re-asking the same question on small talk.
        """
        # If the message contains pet/symptom keywords it is NOT purely social
        if self._PET_OR_SYMPTOM_WORDS_RE.search(text):
            return False
        # If any social pattern matches, it IS social
        for pattern in _SOCIAL_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @staticmethod
    def _extract_owner_name(text: str) -> str:
        """Extract owner's first name from a greeting message, or ''."""
        m = _NAME_FROM_GREETING_RE.search(text)
        if m:
            name = m.group(1).strip().capitalize()
            # Exclude common non-name words that match the pattern
            EXCLUDED = {'fine', 'ok', 'okay', 'good', 'great', 'well', 'here',
                        'glad', 'happy', 'sorry', 'back', 'home', 'there'}
            if name.lower() not in EXCLUDED:
                return name
        return ''

    # ------------------------------------------------------------------
    # Pre-intake guardrails: fast deterministic screen before LLM call
    # ------------------------------------------------------------------
    _DECEASED_PATTERNS = [
        r'\b(died|passed\s+away|passed\s+on|put\s+(him|her|it|them|my\s+\w+)\s+(down|to\s+sleep)|euthaniz\w*|rainbow\s+bridge|gone\s+to\s+heaven|in\s+heaven)\b',
    ]
    _HUMAN_SUBJECT_PATTERNS = [
        r'\bmy\s+human\b',
        r'\bmy\s+(person|child|kid|son|daughter|husband|wife|partner|mom|mother|dad|father|brother|sister|friend|grandma|grandpa|grandfather|grandmother|parent)\b.{0,30}\b(sick|ill|not\s+well|unwell|hurt|pain|ache|injur|vomit|cough|fever)',
        r"\b(i\s+am|i'm|i\s+feel|i\s+don't\s+feel)\s+.{0,15}\b(sick|ill|not\s+well|unwell|nauseous)\b",
    ]
    _NORMAL_BEHAVIOR_PATTERNS = [
        r'\b(humping|mounting|mating\s+with|humps|mounts|mates\s+with)\b',
    ]
    # Non-illness general pet Q&A — scope boundary for clinic triage tool.
    # Only fires when NO medical symptom words are present in the same message.
    # Patterns match clear general-care requests: food, diet, training, grooming,
    # breed info, pricing, registration. NOT medical: "won't eat" IS medical.
    _NON_ILLNESS_PATTERNS = [
        # Food / diet / nutrition (not "won't eat" — that's medical)
        r'\b(what\s+(should|can|do)\s+i\s+(feed|give)\b|best\s+(food|diet)\s+for|can\s+(dogs?|cats?|pets?)\s+eat|is\s+\w+\s+(safe|ok|okay|good)\s+to\s+(eat|feed)|how\s+much\s+(should\s+i\s+feed|food\s+does))\b',
        # Training / obedience
        r'\b(how\s+(do\s+i|to)\s+(train|teach|stop|get)\s+(my\s+)?(dog|cat|puppy|kitten|pet)\b|potty\s+train|house\s+train|crate\s+train|obedience\s+(class|training)|how\s+do\s+i\s+stop\s+(my\s+)?(dog|cat)\s+from\s+(bark|bite|jump|pull|chew|scratch))\b',
        # Grooming (not associated with medical symptoms)
        r'\b(how\s+(often|do\s+i|should\s+i).{0,20}\b(groom|bathe|brush|clip|trim)\b|grooming\s+(tips?|advice|schedule)|how\s+to\s+(bathe|brush|cut|trim)\s+(my\s+)?(dog|cat|pet)s?)\b',
        # Breed info / characteristics
        r'\b(what\s+(breed|type)\s+(is|are)\s+good\s+for|which\s+breed|best\s+breed\s+for|dog\s+breeds?\s+(for|that|which)|breed\s+recommendation)\b',
        # Pet pricing / adoption (clearly non-medical)
        r'\b(how\s+much\s+(does|do)\s+(a\s+)?(dog|cat|puppy|kitten|pet)\s+cost|where\s+(can\s+i\s+)?(adopt|buy|get)\s+(a\s+)?(dog|cat|puppy|kitten|pet))\b',
        # Registration / microchip info questions (non-medical)
        r'\b(how\s+do\s+i\s+(register|microchip|license)\s+(my\s+)?(dog|cat|pet)|pet\s+registration|dog\s+license)\b',
    ]
    _PET_WORDS_RE = r'\b(pet|dog|cat|bird|rabbit|hamster|fish|horse|pony|animal|puppy|kitten|bunny|turtle|snake|lizard|parrot|chicken|duck|goat|cow|pig|sheep|ferret|rat|mouse|frog|gecko|iguana|guinea\s+pig|hamster|gerbil|chinchilla|hedgehog)\b'
    _MEDICAL_WORDS_RE = r'\b(blood|bleed|pain|swollen|swell|vomit|diarrhea|limp|fever|lethargic|not\s+eating|won.t\s+eat|discharge|wound|injur|sick|ill|weak|seizure|tremor|lump|mass|growth|infection|pus|rash|itch|scratch\w*\s+(himself|herself|itself|constantly|excessively))\b'

    def _pre_intake_screen(self, user_message: str):
        """
        Fast deterministic pre-screen before LLM intake.
        Returns a response dict if a guardrail triggers, or None to proceed.

        Categories (checked in priority order):
          1. Abuse / directed threats
          2. Deceased pet → compassionate response
          3. Non-pet subject (human health) → redirect
          4. Normal animal behavior → acknowledge, offer behavioral consult
        """
        msg = user_message.lower().strip()
        lang = self.session.get('language', 'en')
        gs = _GUARDRAIL_STRINGS.get(lang, _GUARDRAIL_STRINGS['en'])

        # 1. Comprehensive guardrail screen
        #    Covers: prompt injection, data extraction, violence/weapons,
        #    sexual/explicit, human-as-pet, substance abuse, abuse/harassment,
        #    trolling/off-topic — in all 7 languages.
        result = guardrails.screen(user_message, lang)
        if result:
            category, label = result
            response_key = _GUARDRAIL_CATEGORY_MAP.get(category, 'abuse')
            logger.info(f"Guardrail: {label} in session {self.session['id']}")
            return self._build_response(
                message=gs.get(response_key, gs['abuse']),
                state='intake',
                agents=['guardrail']
            )

        # 2. Deceased pet
        for pattern in self._DECEASED_PATTERNS:
            if re.search(pattern, msg):
                logger.info(f"Guardrail: deceased pet detected in session {self.session['id']}")
                self.session['state'] = 'complete'
                return self._build_response(
                    message=gs['deceased_pet'],
                    state='complete',
                    agents=['guardrail']
                )

        # 3. Non-pet subject (human health)
        for pattern in self._HUMAN_SUBJECT_PATTERNS:
            if re.search(pattern, msg):
                # Don't trigger if a pet is also mentioned ("my kid stepped on my cat")
                if not re.search(self._PET_WORDS_RE, msg):
                    logger.info(f"Guardrail: non-pet subject in session {self.session['id']}")
                    return self._build_response(
                        message=gs['non_pet'],
                        state='intake',
                        agents=['guardrail']
                    )

        # 4. Normal animal behavior (only if no concurrent medical symptom)
        for pattern in self._NORMAL_BEHAVIOR_PATTERNS:
            if re.search(pattern, msg) and not re.search(self._MEDICAL_WORDS_RE, msg):
                logger.info(f"Guardrail: normal behavior detected in session {self.session['id']}")
                return self._build_response(
                    message=gs['normal_behavior'],
                    state='intake',
                    agents=['guardrail']
                )

        # 5. Non-illness general pet Q&A — clinic triage tool scope boundary.
        #    Redirect food/training/grooming/breed/pricing questions that have
        #    no medical symptom words. Soft redirect, not a hard block.
        #    Only active once we know this isn't an illness query.
        for pattern in self._NON_ILLNESS_PATTERNS:
            if re.search(pattern, msg) and not re.search(self._MEDICAL_WORDS_RE, msg):
                logger.info(f"Scope: non-illness general pet Q&A in session {self.session['id']}")
                return self._build_response(
                    message=gs.get('non_illness_scope', gs['offtopic']),
                    state='intake',
                    agents=['scope_redirect']
                )

        return None

    @traceable(name="orchestrator.process")
    def process(self, user_message: str) -> dict:
        self.start_time = time.time()

        if self.session.get('state') in SessionState.TERMINAL_STATES:
            return self._handle_post_completion(user_message)

        # Pre-intake guardrails: catch abuse, grief, non-pet, normal behavior
        guardrail_response = self._pre_intake_screen(user_message)
        if guardrail_response is not None:
            return guardrail_response

        # ── BUG-03: Social / greeting input ────────────────────────────────
        # If the message is purely social (greeting, pleasantry, name intro)
        # with no pet or symptom content, acknowledge warmly and redirect to
        # the CURRENT unanswered question — never re-ask the same question.
        if self._is_social_input(user_message):
            owner_name = self._extract_owner_name(user_message)
            # Store name in session for future personalization
            if owner_name:
                self.session.setdefault('pet_profile', {}).setdefault('owner_name', owner_name)
            # Use localized greeting so French/Spanish/etc. sessions stay consistent
            if owner_name:
                greeting_str = self._t('greeting_named', name=owner_name)
            else:
                greeting_str = self._t('greeting_anon')

            species_known = self.session.get('pet_profile', {}).get('species', '')
            if species_known:
                redirect_key = 'social_redirect_has_species'
                msg = self._t(redirect_key, greeting=greeting_str, species=species_known)
            else:
                redirect_key = 'social_redirect_no_species'
                msg = self._t(redirect_key, greeting=greeting_str)

            logger.info(
                f"Social input detected in session {self.session['id']} — "
                f"redirecting (owner_name={owner_name!r}, species_known={species_known!r})"
            )
            return self._build_response(
                message=msg,
                state=SessionState.INTAKE,
                agents=['social_redirect']
            )

        # ── BUG-04: Duration pre-extraction ────────────────────────────────
        # Before calling the LLM intake agent, try to extract a duration phrase
        # from the current message with a regex. If found and timeline is not
        # yet stored, pre-populate session.symptoms.timeline so the intake LLM
        # never needs to ask "how long has this been going on?"
        if not self.session.get('symptoms', {}).get('timeline'):
            dur_match = _DURATION_RE.search(user_message)
            if dur_match:
                self.session.setdefault('symptoms', {})['timeline'] = dur_match.group(0).strip()
                logger.info(
                    f"Pre-extracted timeline '{dur_match.group(0).strip()}' "
                    f"in session {self.session['id']}"
                )

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

        # Species keyword detection — two-pass approach:
        #
        # Pass 1 (current message only): always scan the current message for
        # a species keyword, even if the session already has one.  This lets
        # an owner CORRECT a previously stored species (e.g. first said "mouse"
        # by mistake, then clarified "hamster").  The current message takes
        # precedence over history.
        #
        # Pass 2 (full history fallback): if the current message has no species
        # keyword AND the session still lacks one, scan all prior messages too
        # (existing behaviour for "my dog has..." without explicit species word).
        _species_keywords = {
            'dog': ['dog', 'dogs', 'puppy', 'puppies', 'pup', 'pups',
                    'canine', 'hound', 'labrador', 'retriever', 'bulldog',
                    'poodle', 'beagle', 'husky', 'shepherd', 'dachshund',
                    'chihuahua', 'rottweiler', 'doberman', 'pitbull',
                    'chien', 'chienne', 'chiot',       # French
                    'perro', 'perra', 'perrito',       # Spanish
                    'hund', 'welpe',                    # German
                    'cane', 'cagnolino',                # Italian
                    'कुत्ता', 'कुत्ती', 'पिल्ला',       # Hindi
                    'کتا', 'کتی',                       # Urdu
                    'كلب',                               # Arabic
                    '狗', '犬', '小狗'],                   # Chinese
            'cat': ['cat', 'cats', 'kitten', 'kittens', 'kitty', 'kitties',
                    'feline', 'tabby', 'calico', 'siamese', 'persian',
                    'bengal', 'maine coon', 'ragdoll',
                    'chat', 'chatte', 'chaton',         # French
                    'gato', 'gata', 'gatito',           # Spanish
                    'katze', 'kätzchen',                 # German
                    'gatto', 'gattino',                  # Italian
                    'बिल्ली', 'बिल्ला', 'बिल्ली का बच्चा', # Hindi
                    'بلی', 'بلا',                         # Urdu
                    'قطة', 'قط',                          # Arabic
                    '猫', '小猫', '猫咪'],                  # Chinese
            'bird': ['bird', 'birds', 'parrot', 'parakeet', 'budgie',
                     'cockatiel', 'canary', 'finch', 'macaw', 'cockatoo',
                     'chicken', 'chickens', 'rooster', 'hen', 'duck',
                     'ducks', 'goose', 'geese', 'turkey', 'pigeon',
                     'dove', 'lovebird', 'conure', 'african grey',
                     'oiseau', 'perroquet', 'canard',    # French
                     'pájaro', 'ave', 'loro', 'pato',    # Spanish
                     'पक्षी', 'चिड़िया', 'तोता', 'मुर्गी', 'मुर्गा', 'बत्तख',  # Hindi
                     'پرندہ', 'طوطا', 'مرغی', 'مرغا', 'بطخ',              # Urdu
                     'طائر', 'عصفور', 'ببغاء', 'دجاجة', 'ديك', 'بطة',    # Arabic
                     '鸟', '鹦鹉', '鸡', '公鸡', '鸭', '鹅'],               # Chinese
            'rabbit': ['rabbit', 'rabbits', 'bunny', 'bunnies', 'hare',
                       'lapin',                          # French
                       'conejo',                         # Spanish
                       'खरगोश',                           # Hindi
                       'خرگوش',                           # Urdu
                       'أرنب',                            # Arabic
                       '兔子', '兔'],                      # Chinese
            'hamster': ['hamster', 'hamsters', 'gerbil', 'guinea pig',
                        'hámster',                       # Spanish
                        'हैम्स्टर',                        # Hindi
                        'ہیمسٹر',                         # Urdu
                        'هامستر',                         # Arabic
                        '仓鼠'],                           # Chinese
            'reptile': ['reptile', 'lizard', 'gecko', 'iguana', 'snake',
                        'turtle', 'tortoise', 'bearded dragon', 'chameleon',
                        'tortue', 'serpent', 'lézard',   # French
                        'tortuga', 'serpiente', 'lagarto', # Spanish
                        'कछुआ', 'सांप', 'छिपकली',         # Hindi
                        'کچھوا', 'سانپ', 'چھپکلی',        # Urdu
                        'سلحفاة', 'ثعبان', 'سحلية',       # Arabic
                        '龟', '蛇', '蜥蜴'],                # Chinese
            'horse': ['horse', 'horses', 'pony', 'ponies', 'foal',
                      'mare', 'stallion', 'colt', 'filly',
                      'cheval', 'poney',                 # French
                      'caballo', 'yegua',                # Spanish
                      'घोड़ा', 'घोड़ी', 'टट्टू',           # Hindi
                      'گھوڑا', 'گھوڑی',                   # Urdu
                      'حصان', 'فرس',                     # Arabic
                      '马'],                              # Chinese
            'fish': ['fish', 'goldfish', 'betta', 'guppy', 'koi',
                     'aquarium fish', 'tropical fish',
                     'poisson',                          # French
                     'pez',                              # Spanish
                     'मछली',                              # Hindi
                     'مچھلی',                             # Urdu
                     'سمكة',                              # Arabic
                     '鱼'],                               # Chinese
            'other': ['other',                                # EN — explicit "other" selection
                      'autre',                              # French
                      'otro', 'otra',                       # Spanish
                      'अन्य',                                # Hindi
                      'دوسرا', 'دوسری',                      # Urdu
                      'أخرى', 'آخر',                        # Arabic
                      '其他',                                 # Chinese
                      'hedgehog', 'chinchilla', 'rat', 'rats',
                      'mouse', 'mice', 'ferret', 'ferrets',
                      'frog', 'toad', 'goat', 'sheep', 'pig',
                      'piglet', 'cow', 'calf', 'lamb',
                      'hérisson', 'furet', 'souris', 'grenouille', 'chèvre', 'mouton', 'cochon', 'vache', 'veau',  # French
                      'erizo', 'hurón', 'ratón', 'rana', 'cabra', 'oveja', 'cerdo', 'vaca', 'ternero',            # Spanish
                      'चूहा', 'मेंढक', 'बकरी', 'बकरा', 'भेड़', 'सूअर', 'गाय', 'बछड़ा', 'हंस',                    # Hindi
                      'چوہا', 'مینڈک', 'بکری', 'بکرا', 'بھیڑ', 'سور', 'گائے', 'بچھڑا',                          # Urdu
                      'فأر', 'ضفدع', 'ماعز', 'خروف', 'غنم', 'بقرة', 'عجل',                                     # Arabic
                      '鼠', '青蛙', '羊', '猪', '牛'],
        }
        def _detect_species_in(text: str):
            """Return (species_name, matched_keyword) for first match, or (None, None)."""
            for sp_name, kws in _species_keywords.items():
                for kw in kws:
                    if kw in text:
                        return sp_name, kw
            return None, None

        def _apply_species(sp_name, kw):
            """Store detected species into intake_out and session."""
            final_name = kw if kw not in ('bird', 'birds', 'reptile', 'other') else sp_name
            intake_out['species'] = final_name
            self.session.setdefault('pet_profile', {})['species'] = final_name
            intake_out.setdefault('pet_profile', {})['species'] = final_name

        # Pass 1: current message alone — allows species corrections
        cur_lower = user_message.lower()
        detected_species, matched_keyword = _detect_species_in(cur_lower)
        if detected_species:
            _apply_species(detected_species, matched_keyword)
        else:
            # Pass 1b: exotic species fallback — only when NO species is known yet.
            # Handles: "axolotl", "capybara", "sugar glider", "fennec fox" etc.
            # Restricted to initial detection only: once a species is stored, Pass 1
            # (keyword dict) handles corrections. Pass 1b must NOT run on later turns
            # because multi-word symptom messages in any language can look like 2-word
            # animal names (e.g. French "depuis jours" → falsely replaces "chat").
            stored = session_profile.get('species', '')
            _greeting_prefixes = ('hi ', 'hey ', 'hello ', 'hi,', 'hey,', 'hello,',
                                   'hi!', 'hey!', 'hello!')
            _is_greeting_msg = (cur_lower.strip() in ('hi', 'hey', 'hello', 'howdy')
                                 or any(cur_lower.startswith(g) for g in _greeting_prefixes))
            if not stored and not _is_greeting_msg:
                words = [w for w in cur_lower.strip().split()
                         if len(w) > 2 and w not in _COMPLAINT_WORDS]
                if 1 <= len(words) <= 2:
                    candidate = ' '.join(words)
                    is_human = (candidate in _INVALID_SPECIES_HUMANS
                                or any(w in _INVALID_SPECIES_HUMANS for w in words))
                    is_fictional = (candidate in _INVALID_SPECIES_FICTIONAL
                                    or any(w in _INVALID_SPECIES_FICTIONAL for w in words))
                    if not is_human and not is_fictional:
                        intake_out['species'] = candidate
                        self.session.setdefault('pet_profile', {})['species'] = candidate
                        intake_out.setdefault('pet_profile', {})['species'] = candidate
                        detected_species = candidate

            if not detected_species and not intake_out.get('species') and not session_profile.get('species'):
                # Pass 2: scan all prior messages only when species is still unknown
                all_user_text = cur_lower
                for msg in self.session.get('messages', []):
                    if msg.get('role') == 'user':
                        all_user_text += ' ' + str(msg.get('content', '')).lower()
                detected_species, matched_keyword = _detect_species_in(all_user_text)
                if detected_species:
                    _apply_species(detected_species, matched_keyword)

        species_val = intake_out.get('species') or session_profile.get('species', '')
        has_species = bool(species_val)

        # Species validity guardrail — block humans and fictional creatures.
        # Clear the stored species and return a redirect so the intake loop
        # prompts the owner for a real animal name.
        if species_val:
            sv_lower = species_val.lower().strip()
            sv_words = sv_lower.split()
            is_human = (sv_lower in _INVALID_SPECIES_HUMANS
                        or any(w in _INVALID_SPECIES_HUMANS for w in sv_words))
            is_fictional = (sv_lower in _INVALID_SPECIES_FICTIONAL
                            or any(w in _INVALID_SPECIES_FICTIONAL for w in sv_words))
            if is_human or is_fictional:
                # Wipe the bad species from session so it doesn't persist
                self.session.get('pet_profile', {}).pop('species', None)
                msg_key = 'invalid_species_human' if is_human else 'invalid_species_fictional'
                return self._build_response(
                    message=self._t(msg_key),
                    state=SessionState.INTAKE,
                    agents=['species_guardrail']
                )

        raw_complaint = (
            intake_out.get('chief_complaint')
            or session_symptoms.get('chief_complaint')
            or ''
        )
        has_complaint = bool(raw_complaint) and self.intake_agent._is_real_complaint(
            raw_complaint, species_val
        )

        # Pet name tracking — carry forward from session or LLM extraction.
        # Also: if the last assistant question asked for the pet's name and the
        # current user reply is a short non-symptom token, treat it as the name.
        #
        # IMPORTANT: _name_question_asked is calculated BEFORE the complaint
        # fallback so we can guard against treating a pet-name reply (e.g.
        # "Mochi", "hi its Diana") as the chief complaint. Without this guard
        # the complaint fallback would store the reply as the complaint, and
        # the enrichment LLM would then use the owner's name (e.g. "Diana")
        # as if it were the patient's name in its follow-up question.
        _last_asst = ''
        for _m in reversed(self.session.get('messages', [])):
            if _m.get('role') == 'assistant':
                _last_asst = _m.get('content', '').lower()
                break
        _name_question_asked = (
            "name" in _last_asst and
            any(w in _last_asst for w in ("what's your", "what is your", "whats your",
                                           "comment s'appelle", "como se llama",
                                           "叫什么名字", "ما اسم", "का नाम", "کا نام"))
        )

        # Complaint fallback: only runs when we did NOT just ask for the pet's
        # name. If the last question was "what's your cat's name?" and the owner
        # says "Mochi" or "hi its Diana", we must NOT store that as the complaint.
        if not has_complaint and user_message.strip() and not _name_question_asked:
            if self.intake_agent._is_real_complaint(user_message.strip(), species_val):
                raw_complaint = user_message.strip()
                intake_out['chief_complaint'] = raw_complaint
                self.session.setdefault('symptoms', {})['chief_complaint'] = raw_complaint
                has_complaint = True

        # Context-inferred pet name: when the last question asked for the pet's
        # name, accept any short non-empty reply (≤3 words, name-like characters)
        # as the pet name — without the _is_real_complaint guard, which is too
        # permissive and incorrectly rejects 4+ character pet names like "Mochi".
        if (_name_question_asked
                and not session_profile.get('pet_name', '')
                and user_message.strip()
                and len(user_message.strip().split()) <= 3):
            _candidate = user_message.strip().title()
            # For mixed-language inputs like "他叫Milky" or "نامش Milky است",
            # the full string fails the Latin-only regex. Try extracting a
            # capitalized English word as the pet name (fixes ZH-1).
            if not re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s\-']+$", _candidate):
                _mixed = re.search(r'\b([A-Z][a-z]{1,20})\b', _candidate)
                if _mixed:
                    _candidate = _mixed.group(1)
            if len(_candidate) >= 2 and re.match(r"^[A-Za-zÀ-ÖØ-öø-ÿ\s\-']+$", _candidate):
                self.session.setdefault('pet_profile', {})['pet_name'] = _candidate
                session_profile['pet_name'] = _candidate
                intake_out.setdefault('pet_profile', {})['pet_name'] = _candidate
                logger.info(f"Context-inferred pet_name='{_candidate}' in session {self.session['id']}")

        pet_name_val = (
            intake_out.get('pet_profile', {}).get('pet_name', '')
            or session_profile.get('pet_name', '')
        )
        if pet_name_val:
            self.session.setdefault('pet_profile', {})['pet_name'] = pet_name_val
        has_pet_name = bool(pet_name_val)
        # After 2 prompts without a name, skip the requirement (owner may use pronouns)
        pet_name_asked = self.session.get('pet_name_asked', 0)

        # Breed tracking — deterministic: if we just asked for breed, store response directly
        breed_asked = self.session.get('breed_asked', 0)
        if (breed_asked > 0
                and not session_profile.get('breed', '')
                and user_message.strip()
                and len(user_message.strip()) < 80):
            stored_breed = user_message.strip().title()
            self.session.setdefault('pet_profile', {})['breed'] = stored_breed
            session_profile['breed'] = stored_breed
            logger.info(f"Stored breed='{stored_breed}' from direct response in session {self.session['id']}")
        _breed_relevant_species = {
            'dog', 'puppy', 'pup', 'cat', 'kitten', 'kitty',
            'chien', 'chiot', 'chat', 'chaton',
            'perro', 'perrito', 'gato', 'gatito',
        }
        has_breed = bool(session_profile.get('breed', '')
                         or intake_out.get('pet_profile', {}).get('breed', ''))
        breed_relevant = species_val.lower().split()[0] in _breed_relevant_species if species_val else False

        # Track how many times we've asked for clarification to prevent loops
        clarification_count = self.session.get('clarification_count', 0)

        # After 2 failed clarifications, accept whatever the user said and proceed
        if has_species and not has_complaint and clarification_count >= 2 and user_message.strip():
            raw_complaint = user_message.strip()
            intake_out['chief_complaint'] = raw_complaint
            self.session.setdefault('symptoms', {})['chief_complaint'] = raw_complaint
            has_complaint = True
            logger.info(f"Forcing intake complete after {clarification_count} clarifications")

        # ZH-2 guard: even if has_complaint is True, verify the stored complaint
        # is substantively a health concern before entering enrichment. If not,
        # fall through to the else branch to re-ask for symptoms.
        _stored_complaint = self.session.get('symptoms', {}).get('chief_complaint', '')
        if has_complaint and not self.intake_agent._is_real_complaint(_stored_complaint, species_val):
            has_complaint = False

        if has_species and has_complaint and (has_pet_name or pet_name_asked >= 2):
            intake_out['intake_complete'] = True
            intake_out['follow_up_questions'] = []
            intake_out['species'] = species_val
            intake_out['chief_complaint'] = raw_complaint
            self.session['clarification_count'] = 0

            # ---------------------------------------------------------------
            # Adaptive context enrichment: ask ONE complaint-specific
            # follow-up question generated by the intake agent (LLM),
            # rather than a hardcoded timeline→eating→energy script.
            # Capped at MAX_ENRICHMENT_TURNS per session.
            # ---------------------------------------------------------------
            symptom_det = intake_out.get('symptom_details', {})
            sess_symptoms = self.session.get('symptoms', {})

            # Merge LLM-extracted details into session
            for field in ('timeline', 'eating_drinking', 'energy_level'):
                val = symptom_det.get(field, '') or sess_symptoms.get(field, '')
                if val:
                    sess_symptoms[field] = val
                    self.session.setdefault('symptoms', {})[field] = val

            # Ask for breed (dogs/cats) before clinical enrichment — max 1 ask
            if breed_relevant and not has_breed and breed_asked < 1:
                self.session['breed_asked'] = breed_asked + 1
                _sp_disp2 = (
                    species_val if species_val and species_val.lower() not in _GENERIC_SPECIES
                    else 'pet'
                )
                pet_ref = pet_name_val or f'your {_sp_disp2}'
                _breed_qs = {
                    'en': f"What breed is {pet_ref}?",
                    'fr': f"Quelle est la race de {pet_ref} ?",
                    'es': f"¿Cuál es la raza de {pet_ref}?",
                    'zh': f"{pet_ref}是什么品种？",
                    'ar': f"ما سلالة {pet_ref}؟",
                    'hi': f"{pet_ref} की नस्ल क्या है?",
                    'ur': f"{pet_ref} کی نسل کیا ہے؟",
                }
                breed_q = _breed_qs.get(self.session.get('language', 'en'), _breed_qs['en'])
                return self._build_response(message=breed_q, state='intake', agents=agents_executed)

            # Deterministic enrichment answer capture: if we asked an enrichment
            # question last turn, store the user's reply directly without relying
            # on the LLM to re-extract it (fixes EN-2 duplicate question loop).
            _pend_field = self.session.pop('_pending_enrichment_field', None)
            if _pend_field and user_message.strip():
                self.session.setdefault('symptoms', {})[_pend_field] = user_message.strip()

            MAX_ENRICHMENT_TURNS = 2
            enrichment_count = self.session.get('enrichment_count', 0)
            if enrichment_count < MAX_ENRICHMENT_TURNS:
                question = self.intake_agent.enrich_context(self.session)
                if question:
                    # Determine which missing field this question addresses so the
                    # next turn can capture the answer deterministically.
                    _syms = self.session.get('symptoms', {})
                    for _f in ('timeline', 'eating_drinking', 'energy_level'):
                        if not _syms.get(_f):
                            self.session['_pending_enrichment_field'] = _f
                            break
                    self.session['enrichment_count'] = enrichment_count + 1
                    return self._build_response(
                        message=question,
                        state='intake',
                        agents=agents_executed
                    )

            # Enrichment complete or skipped — proceed to safety gate
            self.session['enrichment_count'] = 0
        elif has_species and has_complaint and not has_pet_name:
            # Early Safety Gate pre-check: if red flags are present, skip pet
            # name collection entirely and route to emergency immediately.
            _early_safety = self.safety_gate.process(intake_out)
            if _early_safety['output']['red_flag_detected']:
                self.session['state'] = SessionState.EMERGENCY
                agents_executed.append('safety_gate')
                self.session['agent_outputs']['safety_gate'] = _early_safety
                logger.warning(
                    f"RED FLAG (early check) in session {self.session['id']}: "
                    f"{_early_safety['output']['red_flags']}"
                )
                _emergency_msgs = {
                    'en': "⚠️ EMERGENCY DETECTED: Based on the symptoms you've described, this may be a life-threatening emergency. Please take your pet to the nearest emergency veterinary clinic IMMEDIATELY. Do not wait for a regular appointment.\n\nIf you're unsure where the nearest emergency clinic is, call your regular vet's office — their voicemail often has emergency clinic information.",
                    'fr': "⚠️ URGENCE DÉTECTÉE : D'après les symptômes que vous avez décrits, il pourrait s'agir d'une urgence vitale. Veuillez emmener votre animal à la clinique vétérinaire d'urgence la plus proche IMMÉDIATEMENT. N'attendez pas un rendez-vous régulier.\n\nSi vous ne savez pas où se trouve la clinique d'urgence la plus proche, appelez votre vétérinaire habituel.",
                    'es': "⚠️ EMERGENCIA DETECTADA: Según los síntomas que ha descrito, esto podría ser una emergencia potencialmente mortal. Lleve a su mascota a la clínica veterinaria de emergencia más cercana INMEDIATAMENTE. No espere una cita regular.\n\nSi no sabe dónde está la clínica de emergencia más cercana, llame a su veterinario habitual.",
                    'zh': "⚠️ 检测到紧急情况：根据您描述的症状，这可能是危及生命的紧急情况。请立即将您的宠物带到最近的紧急兽医诊所。不要等待普通预约。\n\n如果您不确定最近的紧急诊所在哪里，请致电您的普通兽医诊所。",
                    'ar': "⚠️ تم اكتشاف حالة طوارئ: بناءً على الأعراض التي وصفتها، قد تكون هذه حالة طوارئ تهدد الحياة. يرجى اصطحاب حيوانك الأليف إلى أقرب عيادة بيطرية طوارئ فوراً. لا تنتظر موعداً عادياً.\n\nإذا لم تكن متأكداً من مكان أقرب عيادة طوارئ، اتصل بعيادة الطبيح البيطري المعتاد.",
                    'hi': "⚠️ आपातकाल का पता चला: आपके द्वारा बताए गए लक्षणों के आधार पर, यह जीवन के लिए खतरनाक आपातकाल हो सकता है। कृपया अपने पालतू जानवर को तुरंत निकटतम आपातकालीन पशु चिकित्सा क्लिनिक में ले जाएँ।\n\nयदि आप निकटतम आपातकालीन क्लिनिक के बारे में अनिश्चित हैं, तो अपने नियमित पशु चिकित्सक को कॉल करें।",
                    'ur': "⚠️ ایمرجنسی کا پتہ چلا: آپ کی بیان کردہ علامات کی بنیاد پر، یہ جان لیوا ایمرجنسی ہو سکتی ہے۔ براہ کرم اپنے پالتو جانور کو فوری طور پر قریب ترین ایمرجنسی ویٹرنری کلینک لے جائیں۔\n\nاگر آپ کو قریب ترین ایمرجنسی کلینک کا پتہ نہیں ہے تو اپنے عام ویٹرنری ڈاکٹر کو کال کریں۔",
                }
                _lang = self.session.get('language', 'en')
                return self._build_response(
                    message=_emergency_msgs.get(_lang, _emergency_msgs['en']),
                    state='emergency',
                    agents=agents_executed,
                    extra={'emergency': True,
                           'red_flags': _early_safety['output']['red_flags']}
                )

            # No red flag — ask for pet name (max 2 times before giving up)
            self.session['pet_name_asked'] = pet_name_asked + 1
            # Use generic fallback for non-specific species words like "other",
            # "otro", "autre" — these produce unnatural phrasing like
            # "what's your other's name?" which confuses owners.
            _GENERIC_SPECIES = {'other', 'otro', 'autre', 'andere', 'altro', 'その他'}
            _sp_display = (
                species_val if species_val and species_val.lower() not in _GENERIC_SPECIES
                else ''
            )
            _name_qs = {
                'en': f"One more thing — what's your {_sp_display or 'pet'}'s name?",
                'fr': f"Une dernière chose — comment s'appelle votre {_sp_display or 'animal'} ?",
                'es': f"Una cosa más — ¿cómo se llama su {_sp_display or 'mascota'}?",
                'zh': f"还有一件事——您的{_sp_display or '宠物'}叫什么名字？",
                'ar': f"شيء أخير — ما اسم {_sp_display or 'حيوانك الأليف'}؟",
                'hi': f"एक और बात — आपके {_sp_display or 'पालतू जानवर'} का नाम क्या है?",
                'ur': f"ایک اور بات — آپ کے {_sp_display or 'پالتو جانور'} کا نام کیا ہے؟",
            }
            name_q = _name_qs.get(self.session.get('language', 'en'), _name_qs['en'])
            return self._build_response(message=name_q, state='intake', agents=agents_executed)
        else:
            self.session['clarification_count'] = clarification_count + 1
            follow_ups = intake_out.get('follow_up_questions', [])

            # Guard: if Pass 1 already detected a species but the intake LLM's
            # follow-up is still asking "what type of pet do you have?", the LLM
            # didn't recognise the species answer (e.g. "other" as a keyword).
            # Override the follow-up with a pet-name question so the conversation
            # moves forward rather than re-asking for the species.
            _SPECIES_ASKS = ('what type of pet', 'what kind of pet', 'quel type d\'animal',
                             'qué tipo de mascota', '什么类型', 'ما نوع', 'किस प्रकार', 'کس قسم')
            if (has_species and follow_ups
                    and any(p in follow_ups[0].lower() for p in _SPECIES_ASKS)):
                # Species is known — skip to pet-name question instead
                pet_name_asked_now = self.session.get('pet_name_asked', 0)
                has_pet_name_now = bool(
                    session_profile.get('pet_name', '')
                    or intake_out.get('pet_profile', {}).get('pet_name', '')
                )
                if not has_pet_name_now and pet_name_asked_now < 2:
                    _GENERIC_SPECIES_FUP = {'other', 'otro', 'autre', 'andere', 'altro'}
                    _sp_fup = (
                        species_val if species_val and species_val.lower() not in _GENERIC_SPECIES_FUP
                        else ''
                    )
                    _lang_now = self.session.get('language', 'en')
                    _override_qs = {
                        'en': f"Thanks! What's your {_sp_fup or 'pet'}'s name?",
                        'fr': f"Merci ! Comment s'appelle votre {_sp_fup or 'animal'} ?",
                        'es': f"¡Gracias! ¿Cómo se llama su {_sp_fup or 'mascota'}?",
                        'zh': f"谢谢！您的{_sp_fup or '宠物'}叫什么名字？",
                        'ar': f"شكراً! ما اسم {_sp_fup or 'حيوانك الأليف'}؟",
                        'hi': f"धन्यवाद! आपके {_sp_fup or 'पालतू जानवर'} का नाम क्या है?",
                        'ur': f"شکریہ! آپ کے {_sp_fup or 'پالتو جانور'} کا نام کیا ہے؟",
                    }
                    self.session['pet_name_asked'] = pet_name_asked_now + 1
                    return self._build_response(
                        message=_override_qs.get(_lang_now, _override_qs['en']),
                        state='intake', agents=agents_executed
                    )

            if follow_ups:
                q = follow_ups[0]
                if isinstance(q, dict):
                    q = q.get('question') or q.get('text') or str(q)
                # Replace generic "your pet/dog/cat" with actual pet name when known
                _pname_now = (
                    intake_out.get('pet_profile', {}).get('pet_name', '')
                    or self.session.get('pet_profile', {}).get('pet_name', '')
                )
                if _pname_now:
                    import re as _re2
                    q = _re2.sub(
                        r'\byour\s+(pet|dog|cat|bird|rabbit|hamster|animal|puppy|kitten)\b',
                        _pname_now, q, flags=_re2.IGNORECASE
                    )
                return self._build_response(
                    message=q,
                    state='intake',
                    agents=agents_executed
                )
            elif not has_species:
                return self._build_response(
                    message=self._t('ask_species'),
                    state='intake',
                    agents=agents_executed
                )
            else:
                # Use pet's name in the fallback symptom question if known
                _pname = self.session.get('pet_profile', {}).get('pet_name', '')
                if _pname:
                    _ask_sym_l = {
                        'en': f"What's going on with {_pname} today?",
                        'fr': f"Qu'est-ce qui se passe avec {_pname} aujourd'hui ?",
                        'es': f"¿Qué le pasa a {_pname} hoy?",
                        'zh': f"{_pname}今天怎么了？",
                        'ar': f"ما الذي يحدث مع {_pname} اليوم؟",
                        'hi': f"{_pname} को आज क्या हो रहा है?",
                        'ur': f"آج {_pname} کو کیا ہو رہا ہے؟",
                    }
                    _lang = self.session.get('language', 'en')
                    _ask_sym = _ask_sym_l.get(_lang, _ask_sym_l['en'])
                else:
                    _ask_sym = self._t('ask_symptoms')
                return self._build_response(
                    message=_ask_sym,
                    state='intake',
                    agents=agents_executed
                )

        # Step 2: SAFETY GATE
        safety_result = self.safety_gate.process(intake_out)
        agents_executed.append('safety_gate')
        self.session['agent_outputs']['safety_gate'] = safety_result

        if safety_result['output']['red_flag_detected']:
            self.session['state'] = SessionState.EMERGENCY
            logger.warning(
                f"RED FLAG DETECTED in session {self.session['id']}: "
                f"{safety_result['output']['red_flags']}"
            )
            guidance_result = self.guidance_agent.process(
                self.session, self.session['agent_outputs']
            )
            agents_executed.append('guidance_summary')
            self.session['agent_outputs']['guidance_summary'] = guidance_result
            # Use localized emergency message instead of hardcoded English
            emergency_msgs = {
                'en': "⚠️ EMERGENCY DETECTED: Based on the symptoms you've described, this may be a life-threatening emergency. Please take your pet to the nearest emergency veterinary clinic IMMEDIATELY. Do not wait for a regular appointment.\n\nIf you're unsure where the nearest emergency clinic is, call your regular vet's office — their voicemail often has emergency clinic information.",
                'fr': "⚠️ URGENCE DÉTECTÉE : D'après les symptômes que vous avez décrits, il pourrait s'agir d'une urgence vitale. Veuillez emmener votre animal à la clinique vétérinaire d'urgence la plus proche IMMÉDIATEMENT. N'attendez pas un rendez-vous régulier.\n\nSi vous ne savez pas où se trouve la clinique d'urgence la plus proche, appelez votre vétérinaire habituel.",
                'es': "⚠️ EMERGENCIA DETECTADA: Según los síntomas que ha descrito, esto podría ser una emergencia potencialmente mortal. Lleve a su mascota a la clínica veterinaria de emergencia más cercana INMEDIATAMENTE. No espere una cita regular.\n\nSi no sabe dónde está la clínica de emergencia más cercana, llame a su veterinario habitual.",
                'zh': "⚠️ 检测到紧急情况：根据您描述的症状，这可能是危及生命的紧急情况。请立即将您的宠物带到最近的紧急兽医诊所。不要等待普通预约。\n\n如果您不确定最近的紧急诊所在哪里，请致电您的普通兽医诊所。",
                'ar': "⚠️ تم اكتشاف حالة طوارئ: بناءً على الأعراض التي وصفتها، قد تكون هذه حالة طوارئ تهدد الحياة. يرجى اصطحاب حيوانك الأليف إلى أقرب عيادة بيطرية طوارئ فوراً. لا تنتظر موعداً عادياً.\n\nإذا لم تكن متأكداً من مكان أقرب عيادة طوارئ، اتصل بعيادة الطبيب البيطري المعتاد.",
                'hi': "⚠️ आपातकाल का पता चला: आपके द्वारा बताए गए लक्षणों के आधार पर, यह जीवन के लिए खतरनाक आपातकाल हो सकता है। कृपया अपने पालतू जानवर को तुरंत निकटतम आपातकालीन पशु चिकित्सा क्लिनिक में ले जाएँ। नियमित अपॉइंटमेंट का इंतजार न करें।\n\nयदि आप निकटतम आपातकालीन क्लिनिक के बारे में अनिश्चित हैं, तो अपने नियमित पशु चिकित्सक को कॉल करें।",
                'ur': "⚠️ ایمرجنسی کا پتہ چلا: آپ کی بیان کردہ علامات کی بنیاد پر، یہ جان لیوا ایمرجنسی ہو سکتی ہے۔ براہ کرم اپنے پالتو جانور کو فوری طور پر قریب ترین ایمرجنسی ویٹرنری کلینک لے جائیں۔ عام ملاقات کا انتظار نہ کریں۔\n\nاگر آپ کو قریب ترین ایمرجنسی کلینک کا پتہ نہیں ہے تو اپنے عام ویٹرنری ڈاکٹر کو کال کریں۔",
            }
            lang = self.session.get('language', 'en')
            esc_msg = emergency_msgs.get(lang, emergency_msgs['en'])
            return self._build_response(
                message=esc_msg,
                state='emergency',
                agents=agents_executed,
                emergency=True
            )

        # Step 3: CONFIDENCE GATE
        # BUG-01 fix: use a SEPARATE counter ('confidence_clarify_count') so
        # confidence-gate loops are capped independently of intake clarification
        # loops.  Sharing 'clarification_count' caused the intake reset (line
        # "self.session['clarification_count'] = 0") to also reset the gate
        # counter, potentially allowing unlimited confidence-gate loops.
        confidence_result = self.confidence_gate.process(intake_out)
        agents_executed.append('confidence_gate')
        self.session['agent_outputs']['confidence_gate'] = confidence_result

        if confidence_result['output']['action'] == 'clarify':
            loop_count = self.session.get('confidence_clarify_count', 0)
            if loop_count < self.MAX_CLARIFICATION_LOOPS:
                self.session['confidence_clarify_count'] = loop_count + 1
                missing = confidence_result['output'].get('missing_required', [])
                return self._build_response(
                    message=self._t('need_more_info', missing=', '.join(missing)),
                    state='intake',
                    agents=agents_executed
                )
            else:
                # Max confidence-gate loops reached — route to receptionist
                self.session['confidence_clarify_count'] = 0
                return self._build_response(
                    message=self._t('connect_receptionist'),
                    state='human_review',
                    agents=agents_executed
                )
        elif confidence_result['output']['action'] == 'human_review':
            return self._build_response(
                message=self._t('conflicting_info'),
                state='human_review',
                agents=agents_executed
            )

        # Step 4: TRIAGE AGENT — include full pet_profile for age/breed/weight context
        triage_result = self.triage_agent.process(
            intake_out, safety_result,
            pet_profile=self.session.get('pet_profile', {})
        )
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

        self.session['state'] = SessionState.COMPLETE

        urgency_raw = triage_result['output'].get('urgency_tier', 'Routine')
        _lang = self.session.get('language', 'en')
        # Localize urgency tier label (fixes ZH-3: "Routine" injected into Chinese sentence)
        urgency = _URGENCY_TIER_LABELS.get(urgency_raw, {}).get(_lang, urgency_raw)
        guidance = guidance_result['output'].get('owner_guidance', {})
        slots = scheduling_result['output'].get('proposed_slots', [])

        # BUG-02 tone fix: personalize with pet name if captured during intake
        pet_name = self.session.get('pet_profile', {}).get('pet_name', '')
        pet_species = self.session.get('pet_profile', {}).get('species', 'pet')
        pet_ref = pet_name if pet_name else f"your {pet_species}"

        message_parts = [
            self._t('recommend_visit', urgency=urgency),
        ]

        if slots:
            message_parts.append(self._t('available_appointments'))
            for s in slots[:3]:
                dt_str = s.get('datetime', '')
                try:
                    dt = datetime.fromisoformat(dt_str)
                    # Use localized date format (fixes ZH-3 English date strings)
                    friendly = _fmt_slot_dt(dt, _lang)
                except (ValueError, TypeError):
                    friendly = dt_str
                message_parts.append(
                    f"  - {friendly} with {s.get('provider')}"
                )

        # BUG-02: include Do tips
        if guidance.get('do'):
            message_parts.append(self._t('while_you_wait'))
            for tip in guidance['do'][:3]:
                message_parts.append(f"  ✓ {tip}")

        # BUG-02: include Don't tips (was missing entirely before)
        if guidance.get('dont'):
            message_parts.append(self._t('dont_do'))
            for tip in guidance['dont'][:2]:
                message_parts.append(f"  ✗ {tip}")

        if guidance.get('watch_for'):
            message_parts.append(self._t('seek_emergency_if'))
            for warn in guidance['watch_for'][:3]:
                message_parts.append(f"  ⚠ {warn}")

        # Offer nearby vet search conversationally
        message_parts.append(self._t('nearby_vets_offer'))

        return self._build_response(
            message='\n'.join(message_parts),
            state='complete',
            agents=agents_executed
        )

    # ------------------------------------------------------------------
    # Post-completion: appointment confirmation, new session, follow-ups
    # ------------------------------------------------------------------
    def _handle_post_completion(self, user_message: str) -> dict:
        msg_lower = user_message.lower().strip()

        # Nearby vet search opt-in — detect conversational trigger
        _nearby_kws = {'nearby', 'find vet', 'find a vet', 'near me', 'local vet',
                       'vet clinic', 'veterinary clinic', 'closest vet',
                       # French
                       'vétérinaire proche', 'trouver un vét',
                       # Spanish
                       'veterinario cerca', 'clínica cercana',
                       # Chinese
                       '附近兽医', '找兽医',
                       # Hindi/Urdu
                       'पास के पशु', 'قریب کے وی'}
        if any(kw in msg_lower for kw in _nearby_kws):
            return self._build_response(
                message='',
                state=self.session.get('state', 'complete'),
                agents=['nearby_vets'],
                extra={'action': 'find_nearby_vets'}
            )

        if any(kw in msg_lower for kw in self._restart_kw):
            for key in list(self.session.keys()):
                if key not in ('id', 'language'):
                    del self.session[key]
            self.session['state'] = SessionState.INTAKE
            self.session['messages'] = []
            self.session['agent_outputs'] = {}
            return self._build_response(
                message=self._t('start_fresh'),
                state=SessionState.INTAKE,
                agents=[]
            )

        sched_out = self.session.get('agent_outputs', {}).get('scheduling', {}).get('output', {})
        slots = sched_out.get('proposed_slots', [])

        # Try to match a slot first — if user mentions a provider, day, or
        # time that matches, that IS booking intent even without "book"/"yes".
        chosen = self._match_slot(msg_lower, slots) if slots else None

        _lang_post = self.session.get('language', 'en')
        if chosen:
            dt_str = chosen.get('datetime', '')
            try:
                dt = datetime.fromisoformat(dt_str)
                friendly = _fmt_slot_dt(dt, _lang_post)
            except (ValueError, TypeError):
                friendly = dt_str
            provider = chosen.get('provider', 'your veterinarian')
            self.session['state'] = SessionState.BOOKED
            self.session['booked_slot'] = chosen
            species = self.session.get('pet_profile', {}).get('species', 'pet')
            return self._build_response(
                message=self._t('appointment_confirmed', time=friendly, provider=provider, species=species),
                state=SessionState.BOOKED,
                agents=['booking_confirmation']
            )

        # User said a booking keyword but we couldn't match a specific slot
        if any(kw in msg_lower for kw in self._book_kw) and slots:
            slot_lines = []
            for i, s in enumerate(slots[:3], 1):
                dt_str = s.get('datetime', '')
                try:
                    dt = datetime.fromisoformat(dt_str)
                    friendly = _fmt_slot_dt(dt, _lang_post)
                except (ValueError, TypeError):
                    friendly = dt_str
                slot_lines.append(f"  {i}. {friendly} with {s.get('provider')}")
            return self._build_response(
                message=self._t('which_appointment', slots='\n'.join(slot_lines)),
                state='complete',
                agents=[]
            )

        if self.session.get('state') == SessionState.BOOKED:
            return self._build_response(
                message=self._t('already_booked'),
                state=SessionState.BOOKED,
                agents=[]
            )

        if slots:
            slot_lines = []
            for i, s in enumerate(slots[:3], 1):
                dt_str = s.get('datetime', '')
                try:
                    dt = datetime.fromisoformat(dt_str)
                    friendly = _fmt_slot_dt(dt, _lang_post)
                except (ValueError, TypeError):
                    friendly = dt_str
                slot_lines.append(f"  {i}. {friendly} with {s.get('provider')}")
            return self._build_response(
                message=self._t('would_you_book', slots='\n'.join(slot_lines)),
                state='complete',
                agents=[]
            )

        return self._build_response(
            message=self._t('triage_complete'),
            state='complete',
            agents=[]
        )

    def _match_slot(self, msg: str, slots: list):
        """Best-effort matching of user message to a proposed slot.

        Handles three selection strategies:
          1. Ordinal references in all 7 supported languages
             ("first"/"premier"/"第一个"/"الأول" → slot 0, etc.)
          2. Score-based matching on day name (all 7 languages), month,
             day-of-month, hour/am-pm, and provider name
          3. Auto-confirm if only one slot was proposed
        """
        # 1. Ordinal references — all 7 supported languages
        # Maps each ordinal keyword to a zero-based slot index.
        ordinals = {
            # English
            'first': 0, '1st': 0, '1': 0,
            'second': 1, '2nd': 1, '2': 1,
            'third': 2, '3rd': 2, '3': 2,
            # French
            'premier': 0, 'première': 0,
            'deuxième': 1, 'second': 1,
            'troisième': 2,
            # Spanish
            'primero': 0, 'primera': 0,
            'segundo': 1, 'segunda': 1,
            'tercero': 2, 'tercera': 2,
            # Chinese (Simplified)
            '第一': 0, '第一个': 0,
            '第二': 1, '第二个': 1,
            '第三': 2, '第三个': 2,
            # Arabic
            'الأول': 0, 'الأولى': 0,
            'الثاني': 1, 'الثانية': 1,
            'الثالث': 2, 'الثالثة': 2,
            # Hindi
            'पहला': 0, 'पहली': 0,
            'दूसरा': 1, 'दूसरी': 1,
            'तीसरा': 2, 'तीसरी': 2,
            # Urdu
            'پہلا': 0, 'پہلی': 0,
            'دوسرا': 1, 'دوسری': 1,
            'تیسرا': 2, 'تیسری': 2,
        }
        for word, idx in ordinals.items():
            if word in msg and idx < len(slots):
                return slots[idx]

        # Day names in all 7 supported languages, keyed by weekday() index (0=Mon).
        # strftime('%A') only produces English, so we maintain this lookup ourselves
        # to support French, Spanish, Chinese, Arabic, Hindi, and Urdu users.
        _DAY_NAMES = {
            0: ['monday',    'lundi',     'lunes',      '星期一', 'الاثنين',   'सोमवार',   'پیر'],
            1: ['tuesday',   'mardi',     'martes',     '星期二', 'الثلاثاء',  'मंगलवार',  'منگل'],
            2: ['wednesday', 'mercredi',  'miércoles',  '星期三', 'الأربعاء',  'बुधवार',   'بدھ'],
            3: ['thursday',  'jeudi',     'jueves',     '星期四', 'الخميس',    'गुरुवार',  'جمعرات'],
            4: ['friday',    'vendredi',  'viernes',    '星期五', 'الجمعة',    'शुक्रवार', 'جمعہ'],
            5: ['saturday',  'samedi',    'sábado',     '星期六', 'السبت',     'शनिवार',   'ہفتہ'],
            6: ['sunday',    'dimanche',  'domingo',    '星期日', 'الأحد',     'रविवार',   'اتوار'],
        }

        # 2. Score each slot by how many components match the message
        best_slot = None
        best_score = 0
        for s in slots:
            score = 0
            dt_str = s.get('datetime', '')
            provider = s.get('provider', '').lower()
            try:
                dt = datetime.fromisoformat(dt_str)
                # Day name match — check all 7 language variants
                for day_name in _DAY_NAMES.get(dt.weekday(), []):
                    if day_name in msg:
                        score += 2
                        break
                # Month name match (English strftime is locale-agnostic)
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
            # Provider name match — full "dr. chen" or just last name "chen"
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

        # 3. Single slot — auto-confirm without requiring explicit selection
        if len(slots) == 1:
            return slots[0]
        return None

    def _build_response(self, message: str, state: str,
                        agents: list, emergency: bool = False,
                        extra: dict = None) -> dict:
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
        response = {
            'message': message,
            'state': state,
            'session_id': self.session['id'],
            'emergency': emergency,
            'metadata': {
                'processing_time_ms': elapsed_ms,
                'agents_executed': agents
            }
        }

        if extra:
            response.update(extra)

        if state in SessionState.TERMINAL_STATES:
            self._fire_webhook(response)

        return response

    def _fire_webhook(self, response: dict):
        """Fire N8N / generic webhook on terminal states (complete/emergency/booked)."""
        url = os.getenv('N8N_WEBHOOK_URL', '').strip()
        if not url:
            return
        payload = {
            'event': response['state'],
            'session_id': response['session_id'],
            'emergency': response['emergency'],
            'pet_profile': self.session.get('pet_profile', {}),
            'agent_outputs': {
                k: v.get('output', {})
                for k, v in self.session.get('agent_outputs', {}).items()
            },
            'booked_slot': self.session.get('booked_slot'),
            'language': self.session.get('language', 'en'),
            'processing_time_ms': response['metadata']['processing_time_ms'],
        }
        try:
            requests.post(url, json=payload, timeout=5)
            logger.info("Webhook fired to %s (event=%s)", url, response['state'])
        except Exception as exc:
            logger.warning("Webhook failed: %s", exc)
