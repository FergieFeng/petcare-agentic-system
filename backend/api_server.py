"""
PetCare Triage & Smart Booking Agent -- API Server

Authors: Syed Ali Turab, Fergie Feng & Diana Liu | Team: Broadview
Date:   March 1, 2026
Code updated: Syed Ali Turab, March 4, 2026 — Orchestrator wiring, optional webhook (non-blocking), requests+threading.

CREDENTIAL AUDIT (March 7, 2026):
  ✓ No hardcoded API keys, passwords, tokens, or secrets in this file.
  ✓ All credentials loaded via os.getenv() at runtime.
  ✓ Full scan across all 16 local + 2 remote branches: CLEAN.
  ✓ Git history (all commits, all branches): no key ever committed.
  ✓ .env is gitignored and never tracked.

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
import sys
import io
import re
import html as _html  # LLM02-2A: HTML entity encoding for API output sanitisation
import json
import uuid
import logging
import tempfile
from datetime import datetime

from functools import wraps
import base64
import time

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from flask import Flask, request, jsonify, send_from_directory, send_file, make_response
import requests as http_requests
import threading
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB upload limit

# ---------------------------------------------------------------------------
# Rate Limiting (Security Audit VULN-06)
# ---------------------------------------------------------------------------
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["60 per minute"],
    storage_uri="memory://",
)

MAX_MESSAGE_LENGTH = 2000
MAX_TTS_LENGTH = 500
MAX_SESSIONS = 10000
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
ALLOWED_AUDIO_TYPES = {'audio/webm', 'audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/mp4'}
VALID_TTS_VOICES = {'alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'}

# ---------------------------------------------------------------------------
# LLM02-2A: Output encoding — sanitise user-supplied pet profile fields
# ---------------------------------------------------------------------------
# The intake agent stores pet_name, breed, age, and weight verbatim from the
# owner's chat messages.  These are returned in the /api/session/<id>/summary
# JSON response.  If the frontend renders any of these fields via innerHTML
# rather than textContent, an owner who typed a name like
#   <script>alert('xss')</script>
# would trigger stored XSS in every browser that loads the summary.
#
# Mitigation: HTML-entity-encode all user-supplied free-text fields before
# they leave the server.  This converts < → &lt;, > → &gt;, " → &quot; etc.,
# making the values safe regardless of how the frontend renders them.
# 'species' is intentionally excluded: it is validated against a known word
# list by the intake agent and is not a free-text injection vector.
# ---------------------------------------------------------------------------
_PET_PROFILE_USER_FIELDS = frozenset({'pet_name', 'breed', 'age', 'weight'})


def _escape_pet_profile(profile: dict) -> dict:
    """
    Return a copy of pet_profile with user-supplied string fields
    HTML-entity-encoded.

    Only fields in _PET_PROFILE_USER_FIELDS are encoded; all other fields
    (including 'species', which is validated) are passed through unchanged.
    Non-string values are also passed through unchanged.

    Called by get_summary() immediately before building the JSON response —
    encoding happens at the output boundary, not at storage time, so the raw
    values remain available for LLM prompts that need to read them.
    """
    result = {}
    for key, value in profile.items():
        if key in _PET_PROFILE_USER_FIELDS and isinstance(value, str):
            # quote=True also escapes single and double quotes, preventing
            # attribute injection if a value is embedded in an HTML attribute.
            result[key] = _html.escape(value, quote=True)
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# LLM07-7B: TTS content policy — block medical impersonation in synthesized audio
# ---------------------------------------------------------------------------
# The /api/voice/synthesize endpoint uses OpenAI TTS to convert arbitrary text
# to MP3 audio.  Even with session-gating and rate limiting (VULN-03 fix), a
# session-authenticated user can request synthesis of text that impersonates a
# veterinarian or contains prescription-level medical instructions.  The
# resulting audio sounds authoritative and can be distributed as "vet advice".
#
# These regex patterns block the three highest-risk content categories:
#   1. Prescription / dosage language   ("give 50mg of amoxicillin twice daily")
#   2. Veterinarian identity claims     ("I am Dr. Smith", "as your veterinarian")
#   3. Named diagnoses in first-person  ("your dog has parvovirus")
#   4. Named antidotes / treatments     ("administer activated charcoal now")
#
# Design choices:
#   • Conservative patterns only — we never block normal guidance language
#     ("keep your pet hydrated", "watch for changes").
#   • Compiled once at module load; matching cost per TTS request is negligible.
#   • This is a server-side last line of defence; it does not replace the
#     guardrails middleware or the rate limiter.
# ---------------------------------------------------------------------------
_TTS_BLOCKED_PATTERNS = [
    # Dosage: a digit followed immediately by a unit of measure.
    # Matches: "50mg", "2.5 ml", "10 cc", "500 mcg", "100 milligrams"
    r'\b\d+(?:\.\d+)?\s*(?:mg|ml|cc|mcg|milligrams?|milliliters?)\b',

    # Prescription verbs: prescribe, prescribed, prescribing, prescription
    r'\bprescri(?:be|bed|bing|ption)\b',

    # "give [pet pronoun/name] [number]" — classic dosage instruction pattern
    r'\bgive\s+(?:him|her|it|your\s+\w+)\s+\d',

    # "administer" followed within 30 chars by a digit
    r'\badminister\b.{0,30}\d',

    # Veterinarian identity claims: "I am Dr. X", "this is Dr. X",
    # "speaking as a veterinarian", "as your vet"
    r'\b(?:i\s+am|this\s+is)\s+(?:dr\.?\s+\w+|a\s+(?:licensed\s+)?veterinarian)\b',
    r'\b(?:as|speaking\s+as)\s+(?:your\s+)?(?:vet(?:erinarian)?|doctor|dr\.?)\b',

    # Named-diagnosis delivery: "your [pet] has [condition-type word]"
    r'\byour\s+(?:pet|dog|cat|animal|[a-z]+)\s+has\s+(?:\w+\s+){0,3}'
    r'(?:disease|syndrome|virus|infection|disorder|condition|cancer|tumou?r)\b',

    # Named antidotes / emergency treatments that only a vet should administer
    r'\b(?:vitamin\s+k[12]?|atropine|apomorphine|activated\s+charcoal|'
    r'naloxone|pralidoxime|ffp|fresh\s+frozen\s+plasma)\b',
]

# Pre-compile all patterns at module load time (re.IGNORECASE covers mixed-case input).
_TTS_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _TTS_BLOCKED_PATTERNS]


def _tts_policy_check(text: str) -> tuple[bool, str]:
    """
    Check text against the TTS content policy.

    Returns:
        (allowed: bool, reason: str)
        allowed=False  → text matched a blocked pattern; do not synthesize.
        reason         → human-readable description of the violation (logged,
                         not sent to the client).

    Called at the top of synthesize_speech(), before any OpenAI API call.
    """
    for pattern in _TTS_COMPILED_PATTERNS:
        match = pattern.search(text)
        if match:
            return False, (
                f"TTS policy violation — pattern '{pattern.pattern[:60]}' "
                f"matched at position {match.start()}: '{match.group()[:40]}'"
            )
    return True, ''

# ---------------------------------------------------------------------------
# HTTP Basic Authentication (credentials from environment variables ONLY)
# ---------------------------------------------------------------------------

def _check_auth(username, password):
    expected_user = os.getenv('AUTH_USERNAME', '')
    expected_pass = os.getenv('AUTH_PASSWORD', '')
    if not expected_user or not expected_pass:
        return False
    return username == expected_user and password == expected_pass


AUTH_EXEMPT_PATHS = ('/api/health', '/health', '/manifest.json', '/sw.js')
AUTH_EXEMPT_PREFIXES = ('/styles/', '/js/', '/icons/', '/images/')
# NOTE: /api/ was removed from AUTH_EXEMPT_PREFIXES as part of
# the security audit (VULN-01, VULN-02).  API endpoints now pass
# through the auth middleware when AUTH_ENABLED=true.


@app.before_request
def require_auth():
    if os.getenv('AUTH_ENABLED', 'false').lower() != 'true':
        return None
    if request.path in AUTH_EXEMPT_PATHS:
        return None
    if any(request.path.startswith(p) for p in AUTH_EXEMPT_PREFIXES):
        return None
    auth = request.authorization
    if auth and _check_auth(auth.username, auth.password):
        return None
    resp = make_response('Authentication required', 401)
    resp.headers['WWW-Authenticate'] = 'Basic realm="PetCare Triage Agent"'
    return resp


@app.after_request
def add_cache_headers(response):
    if request.path.endswith(('.js', '.css', '.html')) or request.path == '/':
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

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
completed_sessions = {}

SESSION_TTL_SECONDS = 3600         # 1 hour for active sessions
COMPLETED_TTL_SECONDS = 86400      # 24 hours for completed (PDF download window)


def _cleanup_sessions():
    now = datetime.utcnow()
    for store, ttl in [(sessions, SESSION_TTL_SECONDS), (completed_sessions, COMPLETED_TTL_SECONDS)]:
        expired = [
            sid for sid, s in store.items()
            if (now - datetime.fromisoformat(s.get('last_activity', s.get('created_at', now.isoformat())))).total_seconds() > ttl
        ]
        for sid in expired:
            del store[sid]
    if expired:
        logger.info(f"Cleaned up {len(expired)} expired sessions")


def _start_cleanup_timer():
    def cleanup_loop():
        while True:
            try:
                _cleanup_sessions()
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
            time.sleep(600)
    cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
    cleanup_thread.start()
    logger.info("Session cleanup timer started (runs every 10 minutes)")

_start_cleanup_timer()


def get_language(lang_code):
    """Return language config, defaulting to English for unsupported codes."""
    if lang_code and lang_code in SUPPORTED_LANGUAGES:
        return lang_code
    return 'en'


# ===========================================================================
# Routes: Static File Serving
# ===========================================================================

_BOOT_TS = str(int(datetime.utcnow().timestamp()))


@app.route('/')
def serve_index():
    """Serve index.html with a dynamic cache-busting token injected into asset URLs."""
    html_path = os.path.join(app.static_folder, 'index.html')
    with open(html_path, 'r') as f:
        html = f.read()
    html = html.replace('{{CACHE_BUST}}', _BOOT_TS)
    resp = make_response(html)
    resp.headers['Content-Type'] = 'text/html; charset=utf-8'
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp


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
# Webhook (optional) — non-blocking after intake complete
# Added March 4, 2026 — Syed Ali Turab. Fires when state is complete or emergency.
# Only active if N8N_WEBHOOK_URL is set (e.g. Slack, email, or any receiver).
# ===========================================================================

def _fire_webhook(session: dict, pipeline_response: dict):
    """
    Fire a non-blocking POST to a configurable webhook after intake completes.

    Payload shape:
      event_type   — "intake_complete" or "emergency_alert"
      session_id   — UUID of the session
      pet_profile  — species, name, age, weight, breed
      triage       — urgency_tier, rationale, confidence
      routing      — appointment_type, providers
      scheduling   — proposed_slots
      red_flags    — red_flag_detected, red_flags list
      owner_guidance — do / dont / watch_for (for reference)
      clinic_summary — full structured JSON (same as /api/session/<id>/summary)
      metadata     — agents_executed, processing_time_ms, language
    """
    # Skip if N8N_WEBHOOK_URL not set (e.g. local dev). No-op is safe.
    webhook_url = os.getenv('N8N_WEBHOOK_URL', '').strip()
    if not webhook_url:
        logger.debug('N8N_WEBHOOK_URL not set — skipping webhook')
        return

    out = session.get('agent_outputs', {})
    # event_type drives downstream routing (e.g. emergency_alert vs intake_complete).
    event_type = 'emergency_alert' if pipeline_response.get('emergency') else 'intake_complete'

    payload = {
        'event_type': event_type,
        'session_id': session.get('id'),
        'language': session.get('language', 'en'),
        'pet_profile': session.get('pet_profile', {}),
        'chief_complaint': session.get('symptoms', {}).get('chief_complaint', ''),
        'triage': out.get('triage', {}).get('output', {}),
        'routing': out.get('routing', {}).get('output', {}),
        'scheduling': out.get('scheduling', {}).get('output', {}),
        'red_flags': out.get('safety_gate', {}).get('output', {}),
        'confidence': out.get('confidence_gate', {}).get('output', {}),
        'owner_guidance': out.get('guidance_summary', {}).get('output', {}).get('owner_guidance', {}),
        'clinic_summary': out.get('guidance_summary', {}).get('output', {}).get('clinic_summary', {}),
        'metadata': {
            'created_at': session.get('created_at'),
            'first_message_at': session.get('first_message_at'),
            'completed_at': datetime.utcnow().isoformat(),
            'agents_executed': list(out.keys()),
            'processing_time_ms': pipeline_response.get('metadata', {}).get('processing_time_ms')
        }
    }

    # Run POST in a daemon thread so the HTTP response is not delayed. (Syed Ali Turab, Mar 4, 2026)
    def _post():
        try:
            r = http_requests.post(webhook_url, json=payload, timeout=8)
            logger.info(f'Webhook fired: event={event_type} status={r.status_code}')
        except Exception as e:
            logger.warning(f'Webhook failed (non-blocking): {e}')

    threading.Thread(target=_post, daemon=True).start()


# ===========================================================================
# Routes: Session Management
# ===========================================================================

@app.route('/api/session/start', methods=['POST'])
@limiter.limit("10 per minute")
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
    if len(sessions) >= MAX_SESSIONS:
        return jsonify({'error': 'Server busy. Please try again later.'}), 503

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
@limiter.limit("20 per minute")
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

    data = request.json or {}
    user_message = data.get('message', '')

    if not user_message or not user_message.strip():
        return jsonify({'error': 'Message is required'}), 400
    if len(user_message) > MAX_MESSAGE_LENGTH:
        return jsonify({'error': f'Message too long (max {MAX_MESSAGE_LENGTH} chars)'}), 400

    session = sessions[session_id]

    if len(session.get('messages', [])) >= 100:
        return jsonify({'error': 'Session message limit reached. Please start a new session.'}), 400

    # Allow language to be changed mid-session
    new_lang = data.get('language')
    if new_lang and new_lang in SUPPORTED_LANGUAGES:
        session['language'] = new_lang

    lang_code = session['language']

    now_iso = datetime.utcnow().isoformat()
    session['messages'].append({
        'role': 'user',
        'content': user_message,
        'timestamp': now_iso,
        'source': data.get('source', 'text'),
        'language': lang_code
    })
    # For baseline comparison: time to complete intake (first message timestamp)
    if not session.get('first_message_at'):
        session['first_message_at'] = now_iso

    from orchestrator import Orchestrator
    _config = {
        'red_flags_path': os.path.join(_BACKEND_DIR, 'data', 'red_flags.json'),
        'clinic_rules_path': os.path.join(_BACKEND_DIR, 'data', 'clinic_rules.json'),
        'slots_path': os.path.join(_BACKEND_DIR, 'data', 'available_slots.json'),
    }
    try:
        orch = Orchestrator(session=session, config=_config)
        response = orch.process(user_message)
    except Exception as e:
        logger.error(f"Pipeline error for session {session_id[:8]}: {e}", exc_info=True)
        return jsonify({'error': 'Internal processing error'}), 500
    response['language'] = lang_code

    session['messages'].append({
        'role': 'assistant',
        'content': response.get('message', ''),
        'timestamp': datetime.utcnow().isoformat(),
        'language': lang_code
    })

    # Fire webhook after pipeline completes (non-blocking, optional). Only when flow reached end or emergency.
    if response.get('state') in ('complete', 'emergency'):
        _fire_webhook(session, response)

    return jsonify(response)


@app.route('/api/session/<session_id>/summary', methods=['GET'])
@limiter.limit("15 per minute")
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
    # Evaluation metrics for baseline comparison (M1–M6): time, required fields, triage, red-flag
    out = session.get('agent_outputs', {})
    cg = out.get('confidence_gate', {}).get('output', {})
    sg = out.get('safety_gate', {}).get('output', {})
    tri = out.get('triage', {}).get('output', {})
    evaluation_metrics = {
        'created_at': session.get('created_at'),
        'first_message_at': session.get('first_message_at'),
        'required_fields_captured_pct': cg.get('required_fields_captured_pct'),
        'red_flag_triggered': sg.get('red_flag_detected', False),
        'triage_urgency_tier': tri.get('urgency_tier'),
    }
    # -------------------------------------------------------------------
    # Security fix (VULN-05): scrub internal agent fields from response.
    # Only return user-facing triage data, NOT raw agent_outputs or messages.
    # -------------------------------------------------------------------
    triage_out = out.get('triage', {}).get('output', {})
    sched_out  = out.get('scheduling', {}).get('output', {})
    guidance   = out.get('guidance_summary', {}).get('output', {})
    safety_out = out.get('safety_gate', {}).get('output', {})

    # LLM02-2A: HTML-encode user-supplied pet_profile fields before they leave
    # the server.  Encoding happens here (output boundary) so the raw values
    # remain available in session state for LLM prompts that read them.
    safe_pet_profile = _escape_pet_profile(session.get('pet_profile', {}))

    return jsonify({
        'session_id': session_id,
        'state': session['state'],
        'language': session.get('language', 'en'),
        'pet_profile': safe_pet_profile,
        'triage_result': {
            'urgency_tier': triage_out.get('urgency_tier'),
            'urgency_label': triage_out.get('urgency_label'),
            'recommended_action': triage_out.get('recommended_action'),
        },
        'scheduling': {
            'proposed_slots': sched_out.get('proposed_slots', []),
        },
        'owner_guidance': guidance.get('owner_guidance', {}),
        'safety_alerts': safety_out.get('red_flag_detected', False),
        'evaluation_metrics': evaluation_metrics,
    })


# ===========================================================================
# Routes: Nearby Vet Finder (Google Places API)
# ===========================================================================

@app.route('/api/nearby-vets', methods=['POST'])
def nearby_vets():
    """
    Find nearby veterinary clinics.

    Tries Google Places API (New) first. If the key is missing or the
    API returns an error, falls back to the OpenStreetMap Overpass API
    which requires no API key.

    Request Body:
        { "lat": 43.65, "lng": -79.38, "radius_km": 5 }
    """
    data = request.json or {}
    lat = data.get('lat')
    lng = data.get('lng')
    radius_km = data.get('radius_km', 5)

    if lat is None or lng is None:
        return jsonify({'error': 'lat and lng are required'}), 400

    try:
        lat, lng = float(lat), float(lng)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid lat/lng values'}), 400

    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return jsonify({'error': 'lat/lng out of valid range'}), 400

    radius_m = min(int(radius_km * 1000), 50000)

    api_key = os.getenv('GOOGLE_MAPS_API_KEY')

    if api_key:
        google_result = _search_google_places(api_key, lat, lng, radius_m, radius_km)
        if google_result is not None:
            return google_result

    osm_result = _search_osm_nominatim(lat, lng, radius_m)
    if osm_result is not None:
        return osm_result

    return jsonify({'error': 'Search failed. Please try again.'}), 500


def _search_google_places(api_key, lat, lng, radius_m, radius_km):
    """Try Google Places API. Attempts the New API first, then legacy. Returns Flask response or None."""
    result = _try_google_places_new(api_key, lat, lng, radius_m, radius_km)
    if result is not None:
        return result
    return _try_google_places_legacy(api_key, lat, lng, radius_m, radius_km)


def _try_google_places_new(api_key, lat, lng, radius_m, radius_km):
    """Google Places API (New) — places.googleapis.com."""
    try:
        field_mask = ','.join([
            'places.displayName', 'places.formattedAddress', 'places.location',
            'places.rating', 'places.userRatingCount',
            'places.nationalPhoneNumber', 'places.internationalPhoneNumber',
            'places.googleMapsUri', 'places.websiteUri',
            'places.currentOpeningHours', 'places.regularOpeningHours',
        ])
        search_resp = http_requests.post(
            'https://places.googleapis.com/v1/places:searchNearby',
            headers={
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': api_key,
                'X-Goog-FieldMask': field_mask,
            },
            json={
                'includedTypes': ['veterinary_care'],
                'maxResultCount': 8,
                'locationRestriction': {
                    'circle': {
                        'center': {'latitude': lat, 'longitude': lng},
                        'radius': float(radius_m),
                    }
                },
            },
            timeout=10,
        )
        data = search_resp.json()
        if 'error' in data:
            logger.warning(f"Places API (New) failed: {data['error'].get('message','')}")
            return None

        results = []
        for place in data.get('places', []):
            loc = place.get('location', {})
            plat, plng_ = loc.get('latitude', 0), loc.get('longitude', 0)
            dist_km = _haversine(lat, lng, plat, plng_)
            cur_h = place.get('currentOpeningHours', {})
            reg_h = place.get('regularOpeningHours', {})
            hours_today = ''
            descs = cur_h.get('weekdayDescriptions', reg_h.get('weekdayDescriptions', []))
            if descs:
                idx = datetime.now().weekday()
                if idx < len(descs):
                    hours_today = descs[idx]
            results.append({
                'name': place.get('displayName', {}).get('text', ''),
                'address': place.get('formattedAddress', ''),
                'rating': place.get('rating'),
                'total_ratings': place.get('userRatingCount', 0),
                'distance_km': round(dist_km, 1),
                'open_now': cur_h.get('openNow', reg_h.get('openNow')),
                'phone': place.get('nationalPhoneNumber', ''),
                'phone_intl': place.get('internationalPhoneNumber', ''),
                'maps_url': place.get('googleMapsUri', ''),
                'website': place.get('websiteUri', ''),
                'hours_today': hours_today,
                'source': 'google',
            })
        results.sort(key=lambda x: x['distance_km'])
        logger.info(f"Google Places (New): {len(results)} vets within {radius_km}km")
        return jsonify({'vets': results, 'count': len(results)})
    except Exception as e:
        logger.warning(f"Places API (New) exception: {e}")
        return None


def _try_google_places_legacy(api_key, lat, lng, radius_m, radius_km):
    """Google Places API (legacy) — maps.googleapis.com."""
    try:
        resp = http_requests.get(
            'https://maps.googleapis.com/maps/api/place/nearbysearch/json',
            params={
                'location': f'{lat},{lng}',
                'radius': radius_m,
                'type': 'veterinary_care',
                'key': api_key,
            },
            timeout=10,
        )
        data = resp.json()
        if data.get('status') not in ('OK', 'ZERO_RESULTS'):
            logger.warning(f"Places legacy failed: {data.get('status')} - {data.get('error_message','')}")
            return None

        results = []
        for place in data.get('results', []):
            loc = place.get('geometry', {}).get('location', {})
            plat, plng_ = loc.get('lat', 0), loc.get('lng', 0)
            dist_km = _haversine(lat, lng, plat, plng_)
            results.append({
                'name': place.get('name', ''),
                'address': place.get('vicinity', ''),
                'rating': place.get('rating'),
                'total_ratings': place.get('user_ratings_total', 0),
                'distance_km': round(dist_km, 1),
                'open_now': place.get('opening_hours', {}).get('open_now'),
                'phone': '',
                'phone_intl': '',
                'maps_url': f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id','')}",
                'website': '',
                'hours_today': '',
                'source': 'google',
            })
        results.sort(key=lambda x: x['distance_km'])
        logger.info(f"Google Places (legacy): {len(results)} vets within {radius_km}km")
        return jsonify({'vets': results, 'count': len(results)})
    except Exception as e:
        logger.warning(f"Places legacy exception: {e}")
        return None


def _search_osm_nominatim(lat, lng, radius_m):
    """Fallback: find vets via OpenStreetMap Nominatim search (no API key needed)."""
    delta = radius_m / 111000.0
    try:
        resp = http_requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={
                'format': 'json',
                'q': 'veterinary clinic',
                'viewbox': f'{lng - delta},{lat + delta},{lng + delta},{lat - delta}',
                'bounded': 1,
                'limit': 10,
                'addressdetails': 1,
                'extratags': 1,
            },
            headers={'User-Agent': 'PetCare-Triage-POC/1.0'},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.error(f"Nominatim search returned {resp.status_code}")
            return None

        data = resp.json()
        results = []
        for place in data:
            plat = float(place.get('lat', 0))
            plng = float(place.get('lon', 0))
            dist_km = _haversine(lat, lng, plat, plng)
            name = place.get('display_name', '').split(',')[0] or 'Veterinary Clinic'
            addr = place.get('address', {})
            extra = place.get('extratags') or {}

            address_parts = []
            for k in ('house_number', 'road', 'city', 'town', 'village',
                       'state', 'postcode'):
                v = addr.get(k)
                if v:
                    address_parts.append(v)

            results.append({
                'name': name,
                'address': ', '.join(address_parts),
                'rating': None,
                'total_ratings': 0,
                'distance_km': round(dist_km, 1),
                'open_now': None,
                'phone': extra.get('phone', extra.get('contact:phone', '')),
                'phone_intl': '',
                'maps_url': f"https://www.openstreetmap.org/?mlat={plat}&mlon={plng}#map=17/{plat}/{plng}",
                'website': extra.get('website', extra.get('contact:website', '')),
                'hours_today': extra.get('opening_hours', ''),
                'source': 'openstreetmap',
            })

        results.sort(key=lambda x: x['distance_km'])
        logger.info(f"Nominatim: found {len(results)} vets within {radius_m}m")
        return jsonify({'vets': results, 'count': len(results)})

    except Exception as e:
        logger.error(f"Nominatim search failed: {e}")
        return None


def _haversine(lat1, lng1, lat2, lng2):
    """Distance in km between two lat/lng points."""
    import math
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lng / 2) ** 2)
    return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_osm_address(tags):
    """Build a human-readable address from OSM tags."""
    parts = []
    for key in ('addr:housenumber', 'addr:street', 'addr:city',
                'addr:state', 'addr:postcode'):
        val = tags.get(key)
        if val:
            parts.append(val)
    return ', '.join(parts) if parts else tags.get('addr:full', '')


# ===========================================================================
# Routes: Export Triage Summary as PDF
# ===========================================================================

@app.route('/api/session/<session_id>/export', methods=['GET'])
@limiter.limit("15 per minute")
def export_summary(session_id):
    """
    Export the triage summary as a downloadable PDF.

    Query Params:
        format: 'pdf' (default)

    Returns:
        PDF file download.
    """
    # Check both active and completed sessions for PDF download persistence
    session = None
    if session_id in sessions:
        session = sessions[session_id]
    elif session_id in completed_sessions:
        session = completed_sessions[session_id]
        logger.info(f"Serving PDF from completed_sessions: {session_id[:8]}...")
    else:
        return jsonify({'error': 'Session not found'}), 404

    # Update last activity to keep session alive longer when PDF is accessed
    if session_id in completed_sessions:
        session['last_pdf_access'] = datetime.utcnow().isoformat()
    pet = session.get('pet_profile', {})
    symptoms = session.get('symptoms', {})
    agent_out = session.get('agent_outputs', {})

    triage_out = agent_out.get('triage', {}).get('output', {})
    routing_out = agent_out.get('routing', {}).get('output', {})
    sched_out = agent_out.get('scheduling', {}).get('output', {})
    guidance_out = agent_out.get('guidance_summary', {}).get('output', {})
    owner_guidance = guidance_out.get('owner_guidance', {})

    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)

        # Branding header
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(0, 6, 'PetCare AI', new_x='LMARGIN', new_y='NEXT', align='R')
        pdf.set_text_color(0, 0, 0)

        # Title
        pdf.set_font('Helvetica', 'B', 18)
        pdf.cell(0, 12, '\xf0\x9f\x90\xbe PetCare Triage Report', new_x='LMARGIN', new_y='NEXT', align='C')
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 6, f'Generated: {datetime.utcnow().strftime("%B %d, %Y at %I:%M %p UTC")}',
                 new_x='LMARGIN', new_y='NEXT', align='C')

        completed_at = session.get('completed_at') or session.get('first_message_at')
        if completed_at:
            try:
                ts = datetime.fromisoformat(str(completed_at))
                pdf.cell(0, 6, f'Triage completed: {ts.strftime("%B %d, %Y at %I:%M %p")}',
                         new_x='LMARGIN', new_y='NEXT', align='C')
            except (ValueError, TypeError):
                pass

        ref_id = f'PC-{session_id[:8].upper()}'
        pdf.cell(0, 6, f'Ref: {ref_id}', new_x='LMARGIN', new_y='NEXT', align='C')
        pdf.ln(8)
        pdf.set_text_color(0, 0, 0)

        # Pet Information
        pdf.set_font('Helvetica', 'B', 13)
        pdf.cell(0, 8, 'Pet Information', new_x='LMARGIN', new_y='NEXT')
        pdf.set_draw_color(37, 99, 235)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font('Helvetica', '', 11)
        _pdf_row(pdf, 'Species', pet.get('species', 'Not specified').title())
        _pdf_row(pdf, 'Name', pet.get('pet_name') or 'Not provided')
        _pdf_row(pdf, 'Breed', pet.get('breed') or 'Not provided')
        _pdf_row(pdf, 'Age', pet.get('age') or 'Not provided')
        pdf.ln(4)

        # Symptoms
        pdf.set_font('Helvetica', 'B', 13)
        pdf.cell(0, 8, 'Presenting Symptoms', new_x='LMARGIN', new_y='NEXT')
        pdf.set_draw_color(37, 99, 235)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font('Helvetica', '', 11)
        chief = symptoms.get('chief_complaint', '')
        routing_categories = {'emergency', 'urgent', 'non-urgent', 'other', 'general', ''}
        if not chief or chief.lower().strip() in routing_categories:
            chief = (agent_out.get('intake', {}).get('output', {})
                     .get('chief_complaint', ''))
        if not chief or chief.lower().strip() in routing_categories:
            msgs = session.get('messages', [])
            species_name = (pet.get('species') or '').lower()
            for m in msgs:
                if m.get('role') == 'user':
                    txt = (m.get('content') or '').strip()
                    if txt and txt.lower() != species_name:
                        chief = txt
                        break
        if not chief:
            chief = 'Not specified'
        _pdf_row(pdf, 'Chief Complaint', chief)
        if symptoms.get('timeline'):
            _pdf_row(pdf, 'Duration', symptoms['timeline'])
        if symptoms.get('eating_drinking'):
            _pdf_row(pdf, 'Eating/Drinking', symptoms['eating_drinking'])
        if symptoms.get('energy_level'):
            _pdf_row(pdf, 'Energy Level', symptoms['energy_level'])
        pdf.ln(4)

        # Triage Result
        pdf.set_font('Helvetica', 'B', 13)
        pdf.cell(0, 8, 'Triage Assessment', new_x='LMARGIN', new_y='NEXT')
        pdf.set_draw_color(37, 99, 235)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)
        pdf.set_font('Helvetica', '', 11)
        urgency = triage_out.get('urgency_tier', 'Not assessed')
        _pdf_row(pdf, 'Urgency Level', urgency)
        if triage_out.get('rationale'):
            _pdf_row(pdf, 'Rationale', triage_out['rationale'])
        factors = triage_out.get('contributing_factors', [])
        if factors:
            _pdf_row(pdf, 'Key Factors', ', '.join(factors))
        pdf.ln(4)

        # Appointments
        slots = sched_out.get('proposed_slots', [])
        if slots:
            pdf.set_font('Helvetica', 'B', 13)
            pdf.cell(0, 8, 'Proposed Appointments', new_x='LMARGIN', new_y='NEXT')
            pdf.set_draw_color(37, 99, 235)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
            pdf.set_font('Helvetica', '', 11)
            for s in slots[:3]:
                dt_str = s.get('datetime', '')
                try:
                    dt = datetime.fromisoformat(dt_str)
                    friendly = dt.strftime('%A, %B %d at %I:%M %p')
                except (ValueError, TypeError):
                    friendly = dt_str
                pdf.cell(0, 6, f'  - {friendly} with {s.get("provider", "TBD")}',
                         new_x='LMARGIN', new_y='NEXT')
            pdf.ln(4)

        # Guidance
        do_tips = owner_guidance.get('do', [])
        watch_for = owner_guidance.get('watch_for', [])
        if do_tips or watch_for:
            pdf.set_font('Helvetica', 'B', 13)
            pdf.cell(0, 8, 'Care Guidance', new_x='LMARGIN', new_y='NEXT')
            pdf.set_draw_color(37, 99, 235)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
            pdf.set_font('Helvetica', '', 11)
            if do_tips:
                pdf.set_font('Helvetica', 'B', 11)
                pdf.cell(0, 6, 'While you wait:', new_x='LMARGIN', new_y='NEXT')
                pdf.set_font('Helvetica', '', 11)
                for tip in do_tips[:5]:
                    pdf.multi_cell(0, 6, f'  - {tip}', new_x='LMARGIN', new_y='NEXT')
                pdf.ln(2)
            if watch_for:
                pdf.set_font('Helvetica', 'B', 11)
                pdf.cell(0, 6, 'Seek emergency care if you notice:', new_x='LMARGIN', new_y='NEXT')
                pdf.set_font('Helvetica', '', 11)
                for w in watch_for[:5]:
                    pdf.multi_cell(0, 6, f'  - {w}', new_x='LMARGIN', new_y='NEXT')
            pdf.ln(4)

        # Disclaimer
        pdf.ln(6)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(120, 120, 120)
        pdf.multi_cell(0, 5,
            'Disclaimer: This triage summary is generated by an AI system and '
            'is not a medical diagnosis. Always consult a licensed veterinarian '
            'for your pet\'s health concerns. This document is for informational '
            'purposes only.')

        pdf_bytes = pdf.output()
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)

        species = re.sub(r'[^a-zA-Z0-9_]', '', pet.get('species', 'pet'))[:20] or 'pet'
        filename = f'petcare_triage_{species}_{session_id[:8]}.pdf'
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True, download_name=filename)

    except ImportError:
        return jsonify({'error': 'PDF generation requires fpdf2 package'}), 503
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        return jsonify({'error': 'Export failed. Please try again.'}), 500


def _pdf_row(pdf, label, value):
    """Helper: write a label-value row in the PDF."""
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(55, 6, f'{label}:', new_x='END')
    pdf.set_font('Helvetica', '', 11)
    pdf.multi_cell(0, 6, str(value), new_x='LMARGIN', new_y='NEXT')


# ===========================================================================
# Routes: Photo Upload & Visual Analysis (OpenAI Vision)
# ===========================================================================

@app.route('/api/session/<session_id>/photo', methods=['POST'])
@limiter.limit("5 per minute")
def analyze_photo(session_id):
    """
    Analyze a pet symptom photo using OpenAI Vision API.

    Request:
        multipart/form-data with 'photo' file field

    Returns:
        JSON with visual observation text (never diagnoses).
    """
    if session_id not in sessions:
        return jsonify({'error': 'Session not found'}), 404

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return jsonify({'error': 'Photo analysis requires OPENAI_API_KEY'}), 503

    if 'photo' not in request.files:
        return jsonify({'error': 'No photo file provided'}), 400

    photo = request.files['photo']

    if photo.content_type not in ALLOWED_IMAGE_TYPES:
        return jsonify({'error': 'Invalid image type. Allowed: JPEG, PNG, WebP, GIF'}), 400

    try:
        from openai import OpenAI

        img_bytes = photo.read()
        b64_img = base64.b64encode(img_bytes).decode('utf-8')
        mime = photo.content_type or 'image/jpeg'

        session = sessions[session_id]
        raw_species = session.get('pet_profile', {}).get('species', 'pet')
        species = re.sub(r'[^a-zA-Z0-9 ]', '', raw_species)[:30] or 'pet'
        lang_code = session.get('language', 'en')
        lang_names = {
            'en': 'English', 'fr': 'French', 'zh': 'Chinese (Mandarin)',
            'ar': 'Arabic', 'es': 'Spanish', 'hi': 'Hindi', 'ur': 'Urdu'
        }
        lang_name = lang_names.get(lang_code, 'English')

        client = OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            max_tokens=400,
            messages=[
                {
                    'role': 'system',
                    'content': (
                        f'You are a veterinary visual observation assistant. '
                        f'Respond in {lang_name}.\n\n'
                        f'RULES:\n'
                        f'1. NEVER name a disease, condition, or diagnosis\n'
                        f'2. NEVER suggest medications\n'
                        f'3. ONLY describe what you visually observe (color, texture, '
                        f'swelling, discharge, area affected)\n'
                        f'4. Note the apparent severity: mild, moderate, or concerning\n'
                        f'5. Suggest the owner mention this to their vet\n'
                        f'6. Keep it to 2-3 sentences'
                    )
                },
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': f'This is a photo of my {species}. '
                                    f'What do you observe about the affected area?'
                        },
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:{mime};base64,{b64_img}',
                                'detail': 'low'
                            }
                        }
                    ]
                }
            ]
        )

        observation = resp.choices[0].message.content.strip()

        session.setdefault('symptoms', {})['photo_observation'] = observation
        session['messages'].append({
            'role': 'system',
            'content': f'[Photo analysis] {observation}',
            'timestamp': datetime.utcnow().isoformat()
        })

        logger.info(f"Photo analyzed for session {session_id[:8]}")
        return jsonify({
            'observation': observation,
            'status': 'success'
        })

    except Exception as e:
        logger.error(f"Photo analysis failed: {e}")
        return jsonify({'error': 'Analysis failed. Please try again.'}), 500


# ===========================================================================
# Routes: Voice Endpoints
# ===========================================================================

@app.route('/api/voice/transcribe', methods=['POST'])
@limiter.limit("5 per minute")
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
    if audio_file.content_type and audio_file.content_type not in ALLOWED_AUDIO_TYPES:
        return jsonify({'error': 'Invalid audio type'}), 400

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
        return jsonify({'error': 'Transcription failed. Please try again.'}), 500


@app.route('/api/voice/synthesize', methods=['POST'])
@limiter.limit("5 per minute")
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

    data = request.json or {}
    text = data.get('text', '')
    voice = data.get('voice', 'nova')

    if voice not in VALID_TTS_VOICES:
        voice = 'nova'

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    if len(text) > MAX_TTS_LENGTH:
        return jsonify({'error': f'Text too long for TTS (max {MAX_TTS_LENGTH} chars)'}), 400

    # Security fix (VULN-03): require a valid session_id to prevent
    # unauthenticated TTS abuse that burns OpenAI API credits.
    session_id = (data.get('session_id') or '').strip()
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Valid session_id required for voice synthesis'}), 400

    # LLM07-7B: TTS content policy — block medical impersonation / prescription
    # language before the text reaches the OpenAI TTS API.  A session-gated but
    # malicious caller could otherwise synthesize audio that sounds like
    # authoritative veterinary advice (dosage instructions, diagnosis delivery,
    # vet identity claims), creating a deepfake distribution pathway.
    # _tts_policy_check() applies conservative regex patterns; normal guidance
    # language passes through unaffected.
    allowed, policy_reason = _tts_policy_check(text)
    if not allowed:
        logger.warning(
            "TTS request blocked by content policy for session %s: %s",
            session_id[:8], policy_reason
        )
        return jsonify({'error': 'Text contains content not permitted for voice synthesis.'}), 400

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        response = client.audio.speech.create(
            model='tts-1-hd',   # HD model: noticeably less robotic, same latency
            voice=voice,
            input=text,
            speed=0.95,         # Slightly slower pacing → more natural, less rushed
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
        return jsonify({'error': 'Synthesis failed. Please try again.'}), 500


# ===========================================================================
# Twilio Click-to-Call (optional)
# Enabled when TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER
# are set.  Initiates an outbound call that connects the user's phone to the
# clinic.  The user's phone rings first; once answered, the clinic is dialled.
# ===========================================================================

def _twilio_enabled():
    return all(os.getenv(k, '').strip() for k in (
        'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_FROM_NUMBER'))

@app.route('/api/twilio/status', methods=['GET'])
def twilio_status():
    return jsonify({'enabled': _twilio_enabled()})

@app.route('/api/call', methods=['POST'])
@limiter.limit("3 per minute")
def initiate_call():
    if not _twilio_enabled():
        return jsonify({'error': 'Twilio is not configured on this server.'}), 503

    data = request.get_json(silent=True) or {}
    clinic_phone = (data.get('clinic_phone') or '').strip()
    user_phone = (data.get('user_phone') or '').strip()

    phone_re = re.compile(r'^\+?[1-9]\d{6,14}$')
    if not phone_re.match(re.sub(r'[\s\-() ]', '', clinic_phone)):
        return jsonify({'error': 'Invalid clinic phone number.'}), 400
    if not phone_re.match(re.sub(r'[\s\-() ]', '', user_phone)):
        return jsonify({'error': 'Invalid user phone number.'}), 400

    try:
        from twilio.rest import Client as TwilioClient
        client = TwilioClient(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        call = client.calls.create(
            to=user_phone,
            from_=os.getenv('TWILIO_FROM_NUMBER'),
            twiml=f'<Response><Say>Connecting you to the veterinary clinic now.</Say><Dial>{clinic_phone}</Dial></Response>'
        )
        logger.info("Twilio call initiated: sid=%s to=%s clinic=%s", call.sid, user_phone, clinic_phone)
        return jsonify({'status': 'calling', 'call_sid': call.sid})
    except ImportError:
        logger.error("twilio package not installed")
        return jsonify({'error': 'Twilio SDK not installed on server.'}), 503
    except Exception as exc:
        logger.error("Twilio call failed: %s", exc)
        return jsonify({'error': 'Failed to initiate call. Please try again.'}), 500


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
        "Supported languages: %s",
        ', '.join(f"{v['name']} ({k})" for k, v in SUPPORTED_LANGUAGES.items())
    )
    logger.info(f"PDF export persistence: {COMPLETED_TTL_SECONDS//3600} hours for completed sessions")

    app.run(host='0.0.0.0', port=port, debug=False)
