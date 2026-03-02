"""
PetCare Triage & Smart Booking Agent -- API Server

Authors: Syed Ali Turab & Fergie Feng | Team: Broadview
Date:   March 1, 2026

Flask-based API server that serves the frontend and handles
intake requests through the orchestrator agent pipeline.

Multilingual Support:
  English (en), French (fr), Chinese (zh), Arabic (ar),
  Spanish (es), Hindi (hi), Urdu (ur)

  The language is passed from the frontend on session start
  and with each message. The LLM is prompted to respond in
  the chosen language. Whisper auto-detects the spoken language
  but the hint improves accuracy.

Endpoints:
  GET  /                              → Serve the chat UI (index.html)
  GET  /api/health                    → Health check with version info
  POST /api/session/start             → Create a new intake session
  POST /api/session/<id>/message      → Send a text message to the agent
  GET  /api/session/<id>/summary      → Retrieve the clinic-facing summary
  POST /api/voice/transcribe          → Transcribe audio via OpenAI Whisper
  POST /api/voice/synthesize          → Convert text to speech via OpenAI TTS
"""

import os
import io
import json
import uuid
import logging
import tempfile
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory, send_file
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# ---------------------------------------------------------------------------
# Logging Setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            os.path.join(os.path.dirname(__file__), 'logs', 'api_server.log')
        )
    ]
)
logger = logging.getLogger('petcare_api')

# ---------------------------------------------------------------------------
# Supported Languages
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES = {
    'en': {
        'name': 'English',
        'whisper_code': 'en',
        'welcome': (
            "Hello! I'm the PetCare Triage Assistant. I'll help you assess "
            "your pet's symptoms and find the right care.\n\n"
            "Let's start — what type of pet do you have (dog, cat, or other)?"
        )
    },
    'fr': {
        'name': 'Français',
        'whisper_code': 'fr',
        'welcome': (
            "Bonjour ! Je suis l'Assistant de Triage PetCare. Je vais vous aider "
            "à évaluer les symptômes de votre animal et trouver les soins adaptés.\n\n"
            "Commençons — quel type d'animal avez-vous (chien, chat, ou autre) ?"
        )
    },
    'zh': {
        'name': '中文',
        'whisper_code': 'zh',
        'welcome': (
            "您好！我是PetCare分诊助手。我将帮助您评估宠物的症状并找到合适的护理。\n\n"
            "让我们开始吧——您养的是什么宠物（狗、猫还是其他）？"
        )
    },
    'ar': {
        'name': 'العربية',
        'whisper_code': 'ar',
        'welcome': (
            "مرحبًا! أنا مساعد فرز رعاية الحيوانات الأليفة. سأساعدك في تقييم "
            "أعراض حيوانك الأليف وإيجاد الرعاية المناسبة.\n\n"
            "لنبدأ — ما نوع حيوانك الأليف (كلب، قطة، أو غير ذلك)؟"
        )
    },
    'es': {
        'name': 'Español',
        'whisper_code': 'es',
        'welcome': (
            "¡Hola! Soy el Asistente de Triaje PetCare. Le ayudaré a evaluar "
            "los síntomas de su mascota y encontrar la atención adecuada.\n\n"
            "Comencemos — ¿qué tipo de mascota tiene (perro, gato u otro)?"
        )
    },
    'hi': {
        'name': 'हिन्दी',
        'whisper_code': 'hi',
        'welcome': (
            "नमस्ते! मैं पेटकेयर ट्राइएज सहायक हूँ। मैं आपके पालतू जानवर के "
            "लक्षणों का मूल्यांकन करने और सही देखभाल खोजने में मदद करूँगा।\n\n"
            "चलिए शुरू करते हैं — आपका पालतू जानवर किस प्रकार का है (कुत्ता, बिल्ली, या अन्य)?"
        )
    },
    'ur': {
        'name': 'اردو',
        'whisper_code': 'ur',
        'welcome': (
            "السلام علیکم! میں پیٹ کیئر ٹرائیج اسسٹنٹ ہوں۔ میں آپ کے پالتو جانور "
            "کی علامات کا جائزہ لینے اور صحیح دیکھ بھال تلاش کرنے میں مدد کروں گا۔\n\n"
            "آئیے شروع کرتے ہیں — آپ کا پالتو جانور کس قسم کا ہے (کتا، بلی، یا کوئی اور)؟"
        )
    }
}

# ---------------------------------------------------------------------------
# In-Memory Session Store
# ---------------------------------------------------------------------------

sessions = {}


def get_language(lang_code):
    """Return language config, defaulting to English for unsupported codes."""
    if lang_code and lang_code in SUPPORTED_LANGUAGES:
        return lang_code
    return 'en'


# ===========================================================================
# Routes: Static File Serving
# ===========================================================================

@app.route('/')
def serve_index():
    """Serve the main frontend page (index.html) from the frontend/ folder."""
    return send_from_directory(app.static_folder, 'index.html')


# ===========================================================================
# Routes: Health Check
# ===========================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    Returns server status, current timestamp, version, voice status,
    and the list of supported languages.
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'voice_enabled': bool(os.getenv('OPENAI_API_KEY')),
        'supported_languages': list(SUPPORTED_LANGUAGES.keys())
    })


# ===========================================================================
# Routes: Session Management
# ===========================================================================

@app.route('/api/session/start', methods=['POST'])
def start_session():
    """
    Start a new intake session.

    Accepts an optional 'language' field in the JSON body.
    Returns a welcome message in the requested language.

    Request Body (optional):
        { "language": "fr" }

    Returns:
        JSON with session_id, welcome message in chosen language, and state.
    """
    data = request.json or {}
    lang_code = get_language(data.get('language', 'en'))
    session_id = str(uuid.uuid4())

    sessions[session_id] = {
        'id': session_id,
        'created_at': datetime.utcnow().isoformat(),
        'language': lang_code,
        'state': 'intake',
        'pet_profile': {},
        'symptoms': {},
        'messages': [],
        'agent_outputs': {},
        'clarification_count': 0
    }

    lang_config = SUPPORTED_LANGUAGES[lang_code]

    logger.info(f"Session started: {session_id} | Language: {lang_config['name']}")

    return jsonify({
        'session_id': session_id,
        'message': lang_config['welcome'],
        'state': 'intake',
        'language': lang_code
    })


@app.route('/api/session/<session_id>/message', methods=['POST'])
def handle_message(session_id):
    """
    Handle an incoming message from the pet owner.

    Accepts a JSON body with 'message' and optional 'language' fields.
    The language can change mid-session (if the user switches in the UI).

    Args:
        session_id: UUID string identifying the active session.

    Request Body:
        {
            "message": "Mon chien vomit depuis hier",
            "language": "fr",
            "source": "text"
        }

    Returns:
        JSON with the agent's response in the session's language.
    """
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404

    data = request.json
    user_message = data.get('message', '')
    session = sessions[session_id]

    # Allow language to be changed mid-session
    new_lang = data.get('language')
    if new_lang and new_lang in SUPPORTED_LANGUAGES:
        session['language'] = new_lang

    lang_code = session['language']

    session['messages'].append({
        'role': 'user',
        'content': user_message,
        'timestamp': datetime.utcnow().isoformat(),
        'source': data.get('source', 'text'),
        'language': lang_code
    })

    # -----------------------------------------------------------------------
    # TODO: Wire up the Orchestrator pipeline here
    #
    # When calling the LLM, include the language instruction:
    #   system_prompt += f"\nRespond in {SUPPORTED_LANGUAGES[lang_code]['name']}."
    #
    # The orchestrator should pass session['language'] to each sub-agent
    # so that LLM-powered agents (Intake, Triage, Guidance) respond in
    # the correct language, while rule-based agents remain language-agnostic.
    # -----------------------------------------------------------------------

    lang_name = SUPPORTED_LANGUAGES[lang_code]['name']

    response = {
        'message': (
            f"[POC STUB] Received: '{user_message}'. "
            f"Language: {lang_name}. "
            "The orchestrator pipeline is not yet implemented. "
            "This is a placeholder response."
        ),
        'state': session['state'],
        'session_id': session_id,
        'language': lang_code
    }

    session['messages'].append({
        'role': 'assistant',
        'content': response['message'],
        'timestamp': datetime.utcnow().isoformat(),
        'language': lang_code
    })

    return jsonify(response)


@app.route('/api/session/<session_id>/summary', methods=['GET'])
def get_summary(session_id):
    """
    Retrieve the clinic-facing summary for a session.

    The summary is always in English (clinic-facing) regardless
    of the session language. The owner-facing guidance is in the
    session's language.
    """
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404

    session = sessions[session_id]
    return jsonify({
        'session_id': session_id,
        'state': session['state'],
        'language': session.get('language', 'en'),
        'pet_profile': session.get('pet_profile', {}),
        'agent_outputs': session.get('agent_outputs', {}),
        'messages': session.get('messages', [])
    })


# ===========================================================================
# Routes: Voice Endpoints
# ===========================================================================

@app.route('/api/voice/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio to text using OpenAI Whisper API (Tier 2 voice).

    Accepts a language hint to improve transcription accuracy.
    Whisper supports all 7 languages natively.

    Request:
        multipart/form-data with 'audio' file field and optional 'language'

    Returns:
        JSON with 'text' (transcribed string) and 'language'.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return jsonify({
            'error': 'Voice transcription requires OPENAI_API_KEY'
        }), 503

    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    lang_code = get_language(request.form.get('language', 'en'))
    whisper_lang = SUPPORTED_LANGUAGES[lang_code]['whisper_code']

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name

        with open(tmp_path, 'rb') as f:
            transcript = client.audio.transcriptions.create(
                model='whisper-1',
                file=f,
                language=whisper_lang,
                response_format='text'
            )

        os.unlink(tmp_path)

        logger.info(
            f"Voice transcribed: {len(transcript)} chars | "
            f"Language: {SUPPORTED_LANGUAGES[lang_code]['name']}"
        )

        return jsonify({
            'text': transcript.strip(),
            'source': 'whisper',
            'language': lang_code
        })

    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return jsonify({'error': f'Transcription failed: {str(e)}'}), 500


@app.route('/api/voice/synthesize', methods=['POST'])
def synthesize_speech():
    """
    Convert text to speech using OpenAI TTS API (Tier 2 voice).

    OpenAI TTS handles multilingual text natively -- it detects
    the language from the input text and synthesizes accordingly.
    No language parameter is needed for TTS.

    Request Body:
        { "text": "Votre animal devrait être vu aujourd'hui.", "voice": "nova" }

    Returns:
        Audio file (MP3) streamed to the client.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return jsonify({
            'error': 'Voice synthesis requires OPENAI_API_KEY'
        }), 503

    data = request.json
    text = data.get('text', '')
    voice = data.get('voice', 'nova')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        response = client.audio.speech.create(
            model='tts-1',
            voice=voice,
            input=text
        )

        audio_bytes = io.BytesIO(response.content)
        logger.info(f"TTS generated: {len(text)} chars, voice={voice}")

        return send_file(
            audio_bytes,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='response.mp3'
        )

    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        return jsonify({'error': f'Synthesis failed: {str(e)}'}), 500


# ===========================================================================
# Server Entry Point
# ===========================================================================

if __name__ == '__main__':
    os.makedirs(os.path.join(os.path.dirname(__file__), 'logs'), exist_ok=True)

    port = int(os.getenv('PORT', 5002))
    debug = os.getenv('APP_ENV', 'development') == 'development'

    logger.info(f"Starting PetCare API server on port {port}")
    logger.info(f"Voice enabled: {bool(os.getenv('OPENAI_API_KEY'))}")
    logger.info(
        f"Supported languages: "
        f"{', '.join(f'{v['name']} ({k})' for k, v in SUPPORTED_LANGUAGES.items())}"
    )

    app.run(host='0.0.0.0', port=port, debug=debug)
