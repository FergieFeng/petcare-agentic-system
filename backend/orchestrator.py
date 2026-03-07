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
import re
from datetime import datetime

# ---------------------------------------------------------------------------
# Localized UI strings for all 7 supported languages.
# These are used for all hardcoded chatbot messages (not LLM-generated).
# ---------------------------------------------------------------------------
_UI_STRINGS = {
    'en': {
        'ask_species': 'What type of pet do you have? (dog, cat, or other)',
        'ask_symptoms': 'Thanks! What symptoms or concerns are you noticing with your pet?',
        'need_more_info': 'I need a bit more information to help you. Could you tell me about: {missing}?',
        'connect_receptionist': 'I want to make sure your pet gets the right care. Let me connect you with our receptionist who can help complete the intake. One moment please.',
        'conflicting_info': 'Some of the information seems conflicting. Let me connect you with our receptionist to ensure we get the most accurate assessment.',
        'recommend_visit': "Based on what you've told me, I'd recommend a **{urgency}** visit.",
        'available_appointments': '\nAvailable appointments:',
        'while_you_wait': '\nWhile you wait:',
        'seek_emergency_if': '\nSeek emergency care if you notice:',
        'start_fresh': "No problem — let's start fresh!\n\nWhat type of pet do you have (dog, cat, or other)?",
        'appointment_confirmed': "Your appointment has been confirmed:\n\n  **{time}** with **{provider}**\n\nPlease bring your {species} and any relevant medical records. If symptoms worsen before the appointment, seek emergency care immediately.\n\nWould you like to start a new session for another concern? Just say **\"start over\"**.",
        'which_appointment': 'Which appointment would you like to book? Please pick one:\n\n{slots}',
        'already_booked': 'Your appointment is already booked! If you\'d like to start a new session, just say **"start over"**.',
        'would_you_book': 'Would you like to book one of these appointments?\n\n{slots}\n\nJust say which one (e.g. **"book the first one"** or **"Tuesday with Dr. Patel"**), or say **"start over"** for a new concern.',
        'triage_complete': 'Your triage is complete. You can say **"start over"** to begin a new session for a different concern.',
    },
    'fr': {
        'ask_species': 'Quel type d\'animal avez-vous ? (chien, chat ou autre)',
        'ask_symptoms': 'Merci ! Quels symptômes ou inquiétudes remarquez-vous chez votre animal ?',
        'need_more_info': 'J\'ai besoin d\'un peu plus d\'informations pour vous aider. Pourriez-vous me parler de : {missing} ?',
        'connect_receptionist': 'Je veux m\'assurer que votre animal reçoive les bons soins. Laissez-moi vous mettre en contact avec notre réceptionniste. Un instant s\'il vous plaît.',
        'conflicting_info': 'Certaines informations semblent contradictoires. Laissez-moi vous mettre en contact avec notre réceptionniste pour assurer l\'évaluation la plus précise.',
        'recommend_visit': "D'après ce que vous m'avez dit, je recommanderais une visite **{urgency}**.",
        'available_appointments': '\nRendez-vous disponibles :',
        'while_you_wait': '\nEn attendant :',
        'seek_emergency_if': '\nConsultez en urgence si vous remarquez :',
        'start_fresh': "Pas de problème — recommençons !\n\nQuel type d'animal avez-vous ? (chien, chat ou autre)",
        'appointment_confirmed': "Votre rendez-vous est confirmé :\n\n  **{time}** avec **{provider}**\n\nVeuillez apporter votre {species} et tout dossier médical pertinent. Si les symptômes s'aggravent avant le rendez-vous, consultez immédiatement un vétérinaire d'urgence.\n\nSouhaitez-vous commencer une nouvelle session ? Dites simplement **\"recommencer\"**.",
        'which_appointment': 'Quel rendez-vous souhaitez-vous réserver ?\n\n{slots}',
        'already_booked': 'Votre rendez-vous est déjà réservé ! Dites **"recommencer"** pour une nouvelle session.',
        'would_you_book': 'Souhaitez-vous réserver l\'un de ces rendez-vous ?\n\n{slots}\n\nDites simplement lequel (par ex. **"réserver le premier"** ou **"mardi avec Dr. Patel"**), ou dites **"recommencer"** pour un autre problème.',
        'triage_complete': 'Votre triage est terminé. Vous pouvez dire **"recommencer"** pour une nouvelle session.',
    },
    'es': {
        'ask_species': '¿Qué tipo de mascota tiene? (perro, gato u otro)',
        'ask_symptoms': '¡Gracias! ¿Qué síntomas o preocupaciones nota en su mascota?',
        'need_more_info': 'Necesito un poco más de información para ayudarle. ¿Podría contarme sobre: {missing}?',
        'connect_receptionist': 'Quiero asegurarme de que su mascota reciba la atención adecuada. Permítame conectarlo con nuestra recepcionista. Un momento por favor.',
        'conflicting_info': 'Parte de la información parece contradictoria. Permítame conectarlo con nuestra recepcionista para asegurar la evaluación más precisa.',
        'recommend_visit': 'Según lo que me ha dicho, recomendaría una visita **{urgency}**.',
        'available_appointments': '\nCitas disponibles:',
        'while_you_wait': '\nMientras espera:',
        'seek_emergency_if': '\nBusque atención de emergencia si nota:',
        'start_fresh': '¡Sin problema — empecemos de nuevo!\n\n¿Qué tipo de mascota tiene? (perro, gato u otro)',
        'appointment_confirmed': 'Su cita ha sido confirmada:\n\n  **{time}** con **{provider}**\n\nPor favor traiga a su {species} y cualquier registro médico relevante. Si los síntomas empeoran antes de la cita, busque atención de emergencia inmediatamente.\n\n¿Desea iniciar una nueva sesión? Simplemente diga **"empezar de nuevo"**.',
        'which_appointment': '¿Qué cita le gustaría reservar?\n\n{slots}',
        'already_booked': '¡Su cita ya está reservada! Diga **"empezar de nuevo"** para una nueva sesión.',
        'would_you_book': '¿Le gustaría reservar una de estas citas?\n\n{slots}\n\nDiga cuál (por ej. **"reservar la primera"** o **"martes con Dr. Patel"**), o diga **"empezar de nuevo"** para otra consulta.',
        'triage_complete': 'Su triage está completo. Puede decir **"empezar de nuevo"** para una nueva sesión.',
    },
    'zh': {
        'ask_species': '您的宠物是什么类型？（狗、猫或其他）',
        'ask_symptoms': '谢谢！您注意到宠物有什么症状或问题？',
        'need_more_info': '我需要更多信息来帮助您。您能告诉我关于：{missing}？',
        'connect_receptionist': '我想确保您的宠物得到正确的护理。让我为您联系我们的接待员。请稍等。',
        'conflicting_info': '部分信息似乎有矛盾。让我为您联系我们的接待员以确保最准确的评估。',
        'recommend_visit': '根据您告诉我的情况，我建议进行 **{urgency}** 就诊。',
        'available_appointments': '\n可用预约：',
        'while_you_wait': '\n等待期间：',
        'seek_emergency_if': '\n如果您注意到以下情况，请立即就医：',
        'start_fresh': '没问题——让我们重新开始！\n\n您的宠物是什么类型？（狗、猫或其他）',
        'appointment_confirmed': '您的预约已确认：\n\n  **{time}** 与 **{provider}**\n\n请携带您的{species}和相关医疗记录。如果症状在预约前恶化，请立即寻求紧急护理。\n\n想要开始新的会话？请说 **"重新开始"**。',
        'which_appointment': '您想预约哪个时间？\n\n{slots}',
        'already_booked': '您的预约已经预订！说 **"重新开始"** 开始新会话。',
        'would_you_book': '您想预约以下哪个时间？\n\n{slots}\n\n请说您想选哪个（如 **"预约第一个"** 或 **"周二与Patel医生"**），或说 **"重新开始"** 处理其他问题。',
        'triage_complete': '您的分诊已完成。您可以说 **"重新开始"** 开始新会话。',
    },
    'ar': {
        'ask_species': 'ما نوع حيوانك الأليف؟ (كلب، قطة، أو غير ذلك)',
        'ask_symptoms': 'شكراً! ما هي الأعراض أو المخاوف التي تلاحظها على حيوانك الأليف؟',
        'need_more_info': 'أحتاج إلى مزيد من المعلومات لمساعدتك. هل يمكنك إخباري عن: {missing}؟',
        'connect_receptionist': 'أريد التأكد من أن حيوانك الأليف يحصل على الرعاية المناسبة. دعني أوصلك بموظف الاستقبال. لحظة من فضلك.',
        'conflicting_info': 'بعض المعلومات تبدو متناقضة. دعني أوصلك بموظف الاستقبال لضمان التقييم الأكثر دقة.',
        'recommend_visit': 'بناءً على ما أخبرتني به، أوصي بزيارة **{urgency}**.',
        'available_appointments': '\nالمواعيد المتاحة:',
        'while_you_wait': '\nأثناء الانتظار:',
        'seek_emergency_if': '\nاطلب رعاية طارئة إذا لاحظت:',
        'start_fresh': 'لا مشكلة — لنبدأ من جديد!\n\nما نوع حيوانك الأليف؟ (كلب، قطة، أو غير ذلك)',
        'appointment_confirmed': 'تم تأكيد موعدك:\n\n  **{time}** مع **{provider}**\n\nيرجى إحضار {species} وأي سجلات طبية ذات صلة. إذا تفاقمت الأعراض قبل الموعد، اطلب رعاية طارئة فوراً.\n\nهل تريد بدء جلسة جديدة؟ قل **"ابدأ من جديد"**.',
        'which_appointment': 'أي موعد تريد حجزه؟\n\n{slots}',
        'already_booked': 'موعدك محجوز بالفعل! قل **"ابدأ من جديد"** لجلسة جديدة.',
        'would_you_book': 'هل تريد حجز أحد هذه المواعيد؟\n\n{slots}\n\nقل أي واحد (مثلاً **"احجز الأول"** أو **"الثلاثاء مع د. باتيل"**)، أو قل **"ابدأ من جديد"** لمشكلة أخرى.',
        'triage_complete': 'اكتمل التقييم. يمكنك قول **"ابدأ من جديد"** لجلسة جديدة.',
    },
    'hi': {
        'ask_species': 'आपका पालतू जानवर किस प्रकार का है? (कुत्ता, बिल्ली, या अन्य)',
        'ask_symptoms': 'धन्यवाद! आप अपने पालतू जानवर में कौन से लक्षण या चिंताएँ देख रहे हैं?',
        'need_more_info': 'आपकी मदद के लिए मुझे थोड़ी और जानकारी चाहिए। क्या आप बता सकते हैं: {missing}?',
        'connect_receptionist': 'मैं यह सुनिश्चित करना चाहता हूँ कि आपके पालतू जानवर को सही देखभाल मिले। मुझे आपको हमारे रिसेप्शनिस्ट से जोड़ने दें। कृपया एक क्षण रुकें।',
        'conflicting_info': 'कुछ जानकारी विरोधाभासी लग रही है। सबसे सटीक मूल्यांकन के लिए मुझे आपको रिसेप्शनिस्ट से जोड़ने दें।',
        'recommend_visit': 'आपने जो बताया उसके आधार पर, मैं **{urgency}** विजिट की सलाह दूँगा।',
        'available_appointments': '\nउपलब्ध अपॉइंटमेंट:',
        'while_you_wait': '\nइंतज़ार करते समय:',
        'seek_emergency_if': '\nयदि आप निम्नलिखित नोटिस करें तो आपातकालीन देखभाल लें:',
        'start_fresh': 'कोई बात नहीं — चलिए नए सिरे से शुरू करते हैं!\n\nआपका पालतू जानवर किस प्रकार का है? (कुत्ता, बिल्ली, या अन्य)',
        'appointment_confirmed': 'आपकी अपॉइंटमेंट की पुष्टि हो गई है:\n\n  **{time}** **{provider}** के साथ\n\nकृपया अपने {species} और किसी भी प्रासंगिक मेडिकल रिकॉर्ड को लाएँ। यदि अपॉइंटमेंट से पहले लक्षण बिगड़ जाएँ, तो तुरंत आपातकालीन देखभाल लें।\n\nक्या आप नया सत्र शुरू करना चाहते हैं? बस **"फिर से शुरू करें"** कहें।',
        'which_appointment': 'आप कौन सी अपॉइंटमेंट बुक करना चाहेंगे?\n\n{slots}',
        'already_booked': 'आपकी अपॉइंटमेंट पहले से बुक है! **"फिर से शुरू करें"** कहें नए सत्र के लिए।',
        'would_you_book': 'क्या आप इनमें से कोई अपॉइंटमेंट बुक करना चाहेंगे?\n\n{slots}\n\nबस बताएँ कौन सी (जैसे **"पहली बुक करें"** या **"मंगलवार Dr. Patel के साथ"**), या **"फिर से शुरू करें"** कहें अन्य समस्या के लिए।',
        'triage_complete': 'आपका ट्राइएज पूरा हो गया है। आप **"फिर से शुरू करें"** कह सकते हैं नए सत्र के लिए।',
    },
    'ur': {
        'ask_species': 'آپ کا پالتو جانور کس قسم کا ہے؟ (کتا، بلی، یا کوئی اور)',
        'ask_symptoms': 'شکریہ! آپ اپنے پالتو جانور میں کیا علامات یا تشویش دیکھ رہے ہیں؟',
        'need_more_info': 'آپ کی مدد کے لیے مجھے تھوڑی اور معلومات چاہیے۔ کیا آپ بتا سکتے ہیں: {missing}؟',
        'connect_receptionist': 'میں یقینی بنانا چاہتا ہوں کہ آپ کے پالتو جانور کو صحیح دیکھ بھال ملے۔ مجھے آپ کو ہمارے ریسپشنسٹ سے جوڑنے دیں۔ ایک لمحہ۔',
        'conflicting_info': 'کچھ معلومات متضاد لگ رہی ہیں۔ سب سے درست تشخیص کے لیے مجھے آپ کو ریسپشنسٹ سے جوڑنے دیں۔',
        'recommend_visit': 'آپ نے جو بتایا اس کی بنیاد پر، میں **{urgency}** وزٹ کی سفارش کروں گا۔',
        'available_appointments': '\nدستیاب ملاقاتیں:',
        'while_you_wait': '\nانتظار کے دوران:',
        'seek_emergency_if': '\nاگر آپ یہ نوٹس کریں تو ایمرجنسی کیئر لیں:',
        'start_fresh': 'کوئی بات نہیں — چلیں نئے سرے سے شروع کرتے ہیں!\n\nآپ کا پالتو جانور کس قسم کا ہے؟ (کتا، بلی، یا کوئی اور)',
        'appointment_confirmed': 'آپ کی ملاقات کی تصدیق ہو گئی ہے:\n\n  **{time}** **{provider}** کے ساتھ\n\nبراہ کرم اپنے {species} اور متعلقہ میڈیکل ریکارڈ لائیں۔ اگر ملاقات سے پہلے علامات بگڑ جائیں تو فوری ایمرجنسی کیئر لیں۔\n\nکیا آپ نیا سیشن شروع کرنا چاہتے ہیں؟ بس **"دوبارہ شروع کریں"** کہیں۔',
        'which_appointment': 'آپ کون سی ملاقات بک کرنا چاہیں گے?\n\n{slots}',
        'already_booked': 'آپ کی ملاقات پہلے سے بک ہے! **"دوبارہ شروع کریں"** کہیں نئے سیشن کے لیے۔',
        'would_you_book': 'کیا آپ ان میں سے کوئی ملاقات بک کرنا چاہیں گے?\n\n{slots}\n\nبس بتائیں کون سی (مثلاً **"پہلی بک کریں"** یا **"منگل Dr. Patel کے ساتھ"**), یا **"دوبارہ شروع کریں"** کہیں کسی اور مسئلے کے لیے۔',
        'triage_complete': 'آپ کا ٹرائیج مکمل ہو گیا ہے۔ آپ نئے سیشن کے لیے **"دوبارہ شروع کریں"** کہ سکتے ہیں۔',
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
                    message=self._t('ask_species'),
                    state='intake',
                    agents=agents_executed
                )
            else:
                return self._build_response(
                    message=self._t('ask_symptoms'),
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
        confidence_result = self.confidence_gate.process(intake_out)
        agents_executed.append('confidence_gate')
        self.session['agent_outputs']['confidence_gate'] = confidence_result

        if confidence_result['output']['action'] == 'clarify':
            loop_count = self.session.get('clarification_count', 0)
            if loop_count < self.MAX_CLARIFICATION_LOOPS:
                self.session['clarification_count'] = loop_count + 1
                missing = confidence_result['output'].get('missing_required', [])
                return self._build_response(
                    message=self._t('need_more_info', missing=', '.join(missing)),
                    state='intake',
                    agents=agents_executed
                )
            else:
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
            self._t('recommend_visit', urgency=urgency),
        ]

        if slots:
            message_parts.append(self._t('available_appointments'))
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
            message_parts.append(self._t('while_you_wait'))
            for tip in guidance['do'][:3]:
                message_parts.append(f"  ✓ {tip}")

        if guidance.get('watch_for'):
            message_parts.append(self._t('seek_emergency_if'))
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
    def _handle_post_completion(self, user_message: str) -> dict:
        msg_lower = user_message.lower().strip()

        if any(kw in msg_lower for kw in self._restart_kw):
            for key in list(self.session.keys()):
                if key not in ('id', 'language'):
                    del self.session[key]
            self.session['state'] = 'intake'
            self.session['messages'] = []
            self.session['agent_outputs'] = {}
            return self._build_response(
                message=self._t('start_fresh'),
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
                message=self._t('appointment_confirmed', time=friendly, provider=provider, species=species),
                state='booked',
                agents=['booking_confirmation']
            )

        # User said a booking keyword but we couldn't match a specific slot
        if any(kw in msg_lower for kw in self._book_kw) and slots:
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
                message=self._t('which_appointment', slots='\n'.join(slot_lines)),
                state='complete',
                agents=[]
            )

        if self.session.get('state') == 'booked':
            return self._build_response(
                message=self._t('already_booked'),
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
                message=self._t('would_you_book', slots='\n'.join(slot_lines)),
                state='complete',
                agents=[]
            )

        return self._build_response(
            message=self._t('triage_complete'),
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
