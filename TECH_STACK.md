# PetCare Triage & Smart Booking Agent -- Technology Stack

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview
**Date:** March 6, 2026

---

## What This Is Built On

The PetCare Agent is a **monolithic Python/Flask application** that bundles the frontend, backend API, orchestrator, and all 7 sub-agents into a **single deployable unit**. It runs inside a **single Docker container** (or directly via Python) and communicates with the OpenAI API for AI reasoning.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Container                           │
│                    (petcare-agent:latest)                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Flask API Server                        │   │
│  │                 (backend/api_server.py)                   │   │
│  │                    Port 5002                              │   │
│  │                                                          │   │
│  │  ┌─────────────┐  ┌──────────────────────────────────┐   │   │
│  │  │  Frontend    │  │  REST API Endpoints              │   │   │
│  │  │  (Static)    │  │                                  │   │   │
│  │  │             │  │  POST /api/session/start          │   │   │
│  │  │  index.html  │  │  POST /api/session/<id>/message  │   │   │
│  │  │  js/app.js   │  │  GET  /api/session/<id>/summary  │   │   │
│  │  │  styles/     │  │  POST /api/voice/transcribe      │   │   │
│  │  │  main.css    │  │  POST /api/voice/synthesize      │   │   │
│  │  └─────────────┘  └──────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │              Orchestrator                        │    │   │
│  │  │         (backend/orchestrator.py)                │    │   │
│  │  │                                                  │    │   │
│  │  │  Coordinates the 7-agent pipeline:               │    │   │
│  │  │                                                  │    │   │
│  │  │  ┌─────────┐ ┌─────────┐ ┌──────────────┐       │    │   │
│  │  │  │ Agent A │→│ Agent B │→│   Agent C    │       │    │   │
│  │  │  │ Intake  │ │ Safety  │ │ Confidence   │       │    │   │
│  │  │  └─────────┘ │  Gate   │ │    Gate      │       │    │   │
│  │  │              └─────────┘ └──────┬───────┘       │    │   │
│  │  │                                 │               │    │   │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────┴───────┐       │    │   │
│  │  │  │ Agent F │←│ Agent E │←│   Agent D   │       │    │   │
│  │  │  │Schedule │ │ Routing │ │   Triage    │       │    │   │
│  │  │  └────┬────┘ └─────────┘ └─────────────┘       │    │   │
│  │  │       │                                         │    │   │
│  │  │  ┌────┴────────────┐                            │    │   │
│  │  │  │    Agent G      │                            │    │   │
│  │  │  │ Guidance+Summary│                            │    │   │
│  │  │  └─────────────────┘                            │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  │  ┌────────────────────────────┐                          │   │
│  │  │  Data Layer (JSON files)   │                          │   │
│  │  │  clinic_rules.json         │                          │   │
│  │  │  red_flags.json            │                          │   │
│  │  │  available_slots.json      │                          │   │
│  │  └────────────────────────────┘                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       │ HTTPS API Calls
                       ▼
        ┌──────────────────────────────┐
        │    External LLM APIs         │
        │                              │
        │  OpenAI API                  │
        │  ├─ GPT-4o-mini             │
        │  ├─ Whisper (STT)            │
        │  ├─ TTS (text-to-speech)     │
        │  └─ Realtime API (Tier 3)    │
        │                              │
        └──────────────────────────────┘
```

---

## How the Agents Are Deployed

All 7 sub-agents run **in-process** within the same Python Flask server. They are **not** separate microservices or separate containers. This is deliberate for the POC:

| Aspect | How It Works |
|--------|-------------|
| **Runtime** | Each agent is a Python class instantiated by the Orchestrator at request time |
| **Execution** | Agents run sequentially within a single HTTP request/response cycle |
| **Communication** | Agents pass data via Python dicts in memory (no network calls between agents) |
| **LLM Calls** | Only agents that need AI reasoning (Intake, Triage, Guidance) call external APIs |
| **Rule-Based Agents** | Safety Gate, Confidence Gate, Routing, Scheduling run locally with zero API cost |
| **State** | Session state is held in-memory (Python dict); shared across agents via Orchestrator |
| **Scaling** | Single process handles all requests; sufficient for POC traffic |

### Agent Execution Flow Per Request

```
1. HTTP Request arrives at Flask server
2. Flask routes to handle_message()
3. Orchestrator is instantiated with the session
4. Orchestrator.process(message) runs:
   ├── IntakeAgent.process()          ← LLM call (OpenAI GPT-4o-mini)
   ├── SafetyGateAgent.process()      ← Local rule-based (no API call)
   ├── ConfidenceGateAgent.process()  ← Local rule-based (no API call)
   ├── TriageAgent.process()          ← LLM call (OpenAI GPT-4o-mini)
   ├── RoutingAgent.process()         ← Local rule-based (no API call)
   ├── SchedulingAgent.process()      ← Local rule-based (no API call)
   └── GuidanceSummaryAgent.process() ← LLM call (OpenAI GPT-4o-mini)
5. Orchestrator assembles response
6. Flask returns JSON response
```

**LLM calls per intake session:** ~3-5 API calls (Intake, Triage, Guidance). Safety Gate, Confidence Gate, Routing, and Scheduling are all rule-based and run locally with zero latency and zero cost.

### Why Not Microservices?

For a POC, a monolithic architecture is the right choice:

| Microservices | Monolith (our approach) |
|--------------|------------------------|
| Each agent = separate container | All agents in one container |
| Inter-agent network calls | In-process function calls |
| Complex orchestration (message queues, service mesh) | Simple Python method calls |
| Higher infra cost (7+ containers) | Single container ($0/mo on free tier) |
| Harder to debug | Easy to debug (single process) |
| Production-ready scaling | POC-appropriate scaling |

**If this moves beyond POC**, the agents are already modular Python classes with standardized I/O contracts. **We do not use an agent framework (Google ADK or LangGraph) for the POC** — the custom Python orchestrator is sufficient, simpler to debug, and matches the assignment’s emphasis on simplicity. For production, orchestration could be formalized in **LangGraph** (same flow, explicit graph, checkpointing); **Google ADK is not recommended** (Vertex AI–centric, off our stack). Migrating to microservices would mean wrapping each agent in an API; agent logic would not change.

---

## Docker Container Architecture

### What the Container Includes

```
petcare-agent:latest
├── Base: python:3.11-slim (Debian Bookworm, ~150MB)
├── Python packages: flask, openai, pydantic, gunicorn (~200MB)
├── Application code: backend/ + frontend/ + docs/ + data/ (~2MB)
├── Total image size: ~350-400MB
└── Exposed port: 5002
```

### Container Runtime Behavior

| Setting | Value | Why |
|---------|-------|-----|
| **Base image** | `python:3.11-slim` | Small footprint, production-ready Python |
| **Port** | 5002 | Matches the Flask server default |
| **Environment** | `APP_ENV=production` | Disables Flask debug mode |
| **Secrets** | Injected via `--env-file .env` | API keys never baked into the image |
| **Persistence** | None (stateless) | Sessions live in-memory; lost on restart |
| **Health check** | `GET /api/health` | Returns `{"status": "ok"}` |
| **Startup time** | ~3-5 seconds | Flask + import time |
| **Memory** | ~100-200MB at idle | Increases with concurrent sessions |

### Docker Build Process

```dockerfile
FROM python:3.11-slim                    # 1. Start from slim Python image
COPY requirements.txt .                  # 2. Copy dependency list
RUN pip install --no-cache-dir -r ...    # 3. Install Python packages
COPY . .                                 # 4. Copy application code
EXPOSE ${PORT:-5002}                     # 5. Declare the port
CMD gunicorn --bind 0.0.0.0:${PORT}     # 6. Start Gunicorn (production WSGI)
    --workers 2 --timeout 120
    backend.api_server:app
```

The build is **deterministic**: same code + same requirements.txt = same image every time. No compiled assets or build steps needed (frontend is vanilla HTML/CSS/JS).

---

## Core Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Language** | Python | 3.10+ (3.11 in Docker) | All server-side logic, agent implementations |
| **Web Framework** | Flask | latest | REST API, static file serving, session management |
| **Frontend** | HTML5 / CSS3 / JavaScript (ES6+) + Inter font | -- | Chat UI, voice controls, responsive design |
| **UI Framework** | Vanilla CSS with CSS variables | -- | Warm teal theme, dark mode, RTL support |
| **Icons/Graphics** | SVG + Emoji | -- | Paw avatars, send button, status indicators |
| **Containerization** | Docker | latest | Reproducible builds, single-container deployment |
| **Process Model** | Single-process, single-threaded | -- | Flask dev server (use Gunicorn for production) |

---

## Frontend Architecture

The frontend is a **single-page application** built entirely with vanilla HTML5, CSS3, and JavaScript (ES6+) — no React, no Vue, no build tools. Flask serves the static files directly. This was a deliberate choice: zero build complexity, instant iteration, and no framework lock-in.

### File Structure

```
frontend/
├── index.html          # Single HTML page — chat UI, header, modals, onboarding
├── js/
│   └── app.js          # All client-side logic (~2,500 lines)
├── styles/
│   └── main.css        # All styling (~1,200 lines) — theme, dark mode, RTL
├── manifest.json       # PWA web app manifest
├── sw.js               # Service worker for offline/PWA support
└── icons/
    ├── icon-192.png    # PWA icon (192×192)
    └── icon-512.png    # PWA icon (512×512)
```

### Design System

| Element | Implementation | Details |
|---------|---------------|---------|
| **Color palette** | CSS custom properties (`--primary: #0d9488`) | Warm teal/emerald — veterinary-appropriate, distinct from generic blue tech |
| **Typography** | [Inter](https://fonts.google.com/specimen/Inter) via Google Fonts | Clean, professional, highly legible at all sizes |
| **Header** | CSS gradient (`#0f766e → #0d9488`) | Branded paw logo with faint watermark backdrop |
| **Chat bubbles** | Flexbox layout with directional alignment | User = right-aligned teal; Assistant = left-aligned with paw avatar circle |
| **Send button** | Circular button with inline SVG arrow | Replaces text "Send" — feels like a modern messaging app |
| **Background** | Subtle radial-dot pattern via CSS `radial-gradient` | Adds visual depth without distracting from content |
| **Cards** | Consistent styling for cost, feedback, reminders, breed risk | Rounded corners, soft shadows, teal accent borders |
| **Dark mode** | CSS variables swap via `.dark-mode` class | Warm tones (`#1a2332` bg, `#e2e8f0` text) — not cold blue-black |
| **RTL support** | `dir="rtl"` set dynamically via JS | Arabic and Urdu flip entire layout (bubbles, input, header) |
| **Scrollbar** | Custom WebKit scrollbar styling | Thin, teal-tinted, matches theme |

### JavaScript Architecture (`app.js`)

All frontend logic lives in a single `app.js` file organized into logical sections:

| Section | Functions | What It Does |
|---------|-----------|-------------|
| **Core Chat** | `sendMessage()`, `addMessage()`, `_streamText()` | Message send/receive, character-by-character streaming display |
| **Voice** | `toggleVoice()`, `startListening()`, `speakResponse()` | 3-tier voice: Browser Speech API → Whisper/TTS → (Realtime stretch) |
| **Internationalization** | `t()`, `setLanguage()`, `LANGUAGES{}` | Translation helper function + full UI string sets for 7 languages |
| **Vet Finder** | `findNearbyVets()`, `_showLocationFallback()`, `_findVetsByCity()` | Google Places API + geolocation + manual city fallback + default location |
| **Photo Upload** | `uploadPhoto()` | Camera/file upload → OpenAI Vision → observation (never diagnosis) |
| **PDF Export** | `downloadSummary()` | Fetch PDF from backend, handle session expiry gracefully |
| **Pet Profiles** | `loadPetProfile()`, `savePetProfile()` | localStorage persistence across sessions |
| **Symptom History** | `loadHistory()`, `saveToHistory()` | Track past triages in localStorage |
| **Cost Estimator** | `_showCostEstimate()` | Post-triage visit cost ranges by urgency tier |
| **Feedback** | `_showFeedbackPrompt()`, `_submitFeedback()` | 1-5 star rating + optional comment |
| **Reminders** | `_showReminderPrompt()`, `_setReminder()` | Browser Notification API for follow-up reminders |
| **Breed Risks** | `_checkBreedRisks()` | Health risk alerts for 11+ known breeds |
| **Dark Mode** | `toggleDarkMode()` | Toggle via header button, persisted in localStorage |
| **Onboarding** | `checkOnboarding()`, `nextOnboardingStep()` | Animated 3-step walkthrough for first-time users |
| **Transcript** | `downloadTranscript()` | Export full chat conversation as `.txt` file |
| **Consent** | `showConsentBanner()` | PIPEDA/PHIPA-style privacy banner on first load |
| **PWA** | Service worker registration | Installable on mobile, offline chat history |

### How the Frontend Communicates with the Backend

```
Browser (app.js)
    │
    ├── POST /api/session/start          → Create session, get welcome message
    ├── POST /api/session/{id}/message   → Send user message, get agent response
    ├── GET  /api/session/{id}/summary   → Fetch triage summary (JSON)
    ├── GET  /api/session/{id}/export    → Download PDF summary
    ├── POST /api/session/{id}/photo     → Upload photo for Vision analysis
    ├── POST /api/nearby-vets            → Search nearby vet clinics
    ├── POST /api/voice/transcribe       → Send audio → get text (Whisper)
    ├── POST /api/voice/synthesize       → Send text → get audio (TTS)
    └── GET  /api/health                 → Health check
```

All API calls use `fetch()` with JSON payloads. The session ID is stored in a JavaScript variable and passed with every request. There is no client-side routing — it's a single-page chat interface.

### Why No Framework?

| Factor | Framework (React/Vue) | Vanilla JS (our approach) |
|--------|----------------------|--------------------------|
| **Build tooling** | Webpack/Vite/Next required | Zero — just files served by Flask |
| **Bundle size** | 50-200KB+ | 0KB framework overhead |
| **Deployment** | Separate build step | Flask serves files directly |
| **Learning curve** | Team must know React/Vue | Standard JS + DOM APIs |
| **Iteration speed** | Fast with hot reload | Instant — edit and refresh |
| **Sufficient for POC?** | Overkill | Yes — single-page chat app |

For a chat-based POC with one page and one interaction flow, vanilla JS is the right tool. If this moved to production with multiple pages and complex state, migrating to React/Next would be warranted.

---

## AI / LLM Layer

| Component | Technology | Pricing | Used By |
|-----------|-----------|---------|---------|
| **Primary LLM** | OpenAI GPT-4o-mini | ~$0.15/1M input, $0.60/1M output | Intake (A), Triage (D), Guidance (G) |
| **Guardrail Classifier** | OpenAI GPT-4o-mini (Stage 2) | ~$0.15/1M input | `guardrails._llm_classify()` — semantic safety screen on every clean message; production default on |
| **Voice STT** | OpenAI Whisper | $0.006/min | Voice transcription (Tier 2) |
| **Voice TTS** | OpenAI TTS (`tts-1-hd`, `speed=0.95`) | $15/1M chars | Voice synthesis (Tier 2) — HD model, significantly less robotic, natural pacing across all 7 languages |
| **LLM Tracing** | LangSmith | Free tier (50K traces/mo) | Opt-in via `LANGCHAIN_TRACING_V2=true`; traces Intake, Triage, Guidance + guardrail classifier as named child spans |

### Cost Per Intake Session (Estimated)

| Component | Tokens | Cost |
|-----------|--------|------|
| Intake Agent (1-3 LLM calls) | ~2,000 tokens | ~$0.004 |
| Triage Agent (1 LLM call) | ~1,000 tokens | ~$0.002 |
| Guidance Agent (1 LLM call) | ~1,500 tokens | ~$0.003 |
| Guardrail classifier (per clean msg, Stage 2) | ~200 tokens | ~$0.00003 |
| Voice Tier 2 (if used) | 1 min audio | ~$0.02 |
| **Total per session** | | **~$0.01-0.03** |
| **Guardrail classifier overhead (daily, POC traffic)** | | **~$0.10/day** |

---

## Multilingual Support

The system supports **7 languages** out of the box. The user selects their language from a dropdown in the header, and the entire experience -- UI, chat, voice input, and voice output -- switches to that language.

### Supported Languages

| Language | Code | Script | Direction | Whisper | Web Speech API | GPT-4o-mini | TTS |
|----------|------|--------|-----------|---------|---------------|---------|-----|
| **English** | `en` | Latin | LTR | Yes | Yes | Yes | Yes |
| **French** | `fr` | Latin | LTR | Yes | Yes | Yes | Yes |
| **Chinese (Mandarin)** | `zh` | Han | LTR | Yes | Yes (Chrome) | Yes | Yes |
| **Arabic** | `ar` | Arabic | **RTL** | Yes | Partial | Yes | Yes |
| **Spanish** | `es` | Latin | LTR | Yes | Yes | Yes | Yes |
| **Hindi** | `hi` | Devanagari | LTR | Yes | Yes (Chrome) | Yes | Yes |
| **Urdu** | `ur` | Nastaliq | **RTL** | Yes | Limited | Yes | Yes |

### How It Works End-to-End

```
1. User selects language from dropdown (e.g., "🇫🇷 Français")
2. Frontend:
   ├── Switches all UI strings (title, placeholder, buttons, disclaimer)
   ├── Applies RTL layout if Arabic or Urdu
   ├── Sets Web Speech API language code (e.g., "fr-FR")
   └── Sends language code with every API call
3. Backend:
   ├── Stores language in session (can change mid-conversation)
   ├── Returns welcome message in the selected language
   ├── Passes language hint to Whisper for better STT accuracy
   └── LLM prompt includes: "Respond in {language_name}"
4. Voice:
   ├── Whisper: auto-detects language + uses hint for accuracy
   ├── OpenAI TTS: auto-detects language from input text
   └── Browser TTS: uses BCP-47 language tag (e.g., "fr-FR")
5. Clinic Summary: always generated in English (staff-facing)
```

### RTL (Right-to-Left) Support

Arabic and Urdu trigger a full RTL layout transformation:

- `<html dir="rtl">` is set dynamically via JavaScript
- Message bubbles flip (user on left, assistant on right)
- Input area, buttons, and text alignment all reverse
- Arabic Naskh and Urdu Nastaliq fonts are loaded
- The language selector stays in the header (reversed position)

### Cost Impact

Zero additional cost for multilingual support:

| Component | Multilingual Cost | Notes |
|-----------|------------------|-------|
| UI translations | Free | Hardcoded in `app.js` |
| GPT-4o-mini responses | Same token cost | Multilingual is native |
| Whisper STT | Same per-minute cost | All languages supported |
| OpenAI TTS | Same per-character cost | Auto-detects language |
| Browser voice | Free | Language via BCP-47 tag |

---

## Voice Layer

Three tiers of voice interaction:

| Feature | Tier 1: Browser Native | Tier 2: Whisper + TTS (`tts-1-hd`) | Tier 3: Realtime API |
|---------|----------------------|----------------------|---------------------|
| **Cost** | Free | ~$0.02/session | ~$0.50-1.00/session |
| **Latency** | ~100ms (client-side) | ~1-2s (API round-trip) | <500ms (WebSocket) |
| **Quality** | Varies by browser | High (Whisper STT, `tts-1-hd` TTS — significantly less robotic, `speed=0.95`) | Highest (native) |
| **Interruption** | Manual (click to stop) | Manual | Native (natural) |
| **Browser** | Chrome/Edge best | All browsers | All browsers |
| **Feel** | Walkie-talkie | Walkie-talkie | Natural phone call |
| **Implementation** | ~2 hours | ~4 hours | ~8 hours |
| **API Key** | No | Yes (OpenAI) | Yes (OpenAI) |

Recommended: Tier 1 for development, Tier 2 for demo, Tier 3 as stretch goal.

### Voice Safety Requirements

Voice introduces additional clinical risk due to possible transcription errors. The following safeguards are enforced:

#### Critical Field Confirmation
The system must confirm these fields when received via voice:

- Duration of symptoms
- Presence of red-flag symptoms (breathing difficulty, seizures, collapse)
- Species and age

Example confirmation prompt:
> "I heard that your dog has been vomiting for 2 days. Is that correct?"

#### Red-Flag Double Confirmation
If STT detects high-risk keywords:
- Ask explicit confirmation before triggering emergency escalation
- If uncertainty remains after confirmation, escalate anyway (conservative default)

#### Confidence-Based Fallback
If STT confidence score is low:
1. Request repetition of the unclear segment
2. Suggest switching to text input
3. If still unclear, route to human receptionist

Voice should never silently accept low-confidence transcriptions for safety-critical fields.

### Voice Failure Scenarios

The voice layer must handle:

| Scenario | Fallback |
|----------|----------|
| Background noise | Request repetition or text fallback |
| Multiple speakers | Ask owner to speak one at a time |
| Medical term misrecognition | Confirm with simpler phrasing |
| Pet name confusion | Confirm species and name explicitly |
| Accent variability | Whisper handles well; Web Speech API varies |
| Silence / timeout | Prompt with "Are you still there?" |

The system defaults to conservative safety decisions when voice input is ambiguous.

### Voice Testing Requirements

| Test Category | What to Test |
|---------------|-------------|
| **Accent samples** | Test with 3+ accent variations per language |
| **Noise levels** | Test at quiet, moderate, and noisy environments |
| **Red-flag phrases** | Verify all 50+ red flags are caught via voice |
| **Intent extraction** | Confirm symptom details extracted correctly |
| **Urgency classification** | Verify voice-originated intakes triage correctly |
| **Fallback triggers** | Confirm low-confidence → text fallback works |

Metrics to monitor:

| Metric | Target |
|--------|--------|
| Word Error Rate (WER) | < 10% (Whisper), < 15% (Web Speech API) |
| Critical field extraction accuracy | ≥ 95% |
| Urgency misclassification rate | 0% for emergencies |
| Fallback trigger rate | Track (no target -- informational) |

---

## Webhook Automation Layer (Optional)

The backend fires an optional webhook POST after the agent pipeline completes (e.g. when intake finishes or a red flag is detected). This decouples downstream actions (email, Slack, logging) from the agent logic.

### How It Works

```
PetCare Agent completes intake
        │
        │  POST to N8N_WEBHOOK_URL (if configured)
        ▼
┌─────────────────────────────────────────────┐
│         Any Webhook Receiver                │
│  (n8n, Zapier, Slack, custom endpoint)      │
│                                             │
│  Example actions:                           │
│  ├─ Slack → #emergency channel              │
│  ├─ Email → clinic inbox (formatted HTML)   │
│  └─ Google Sheets → intake log              │
└─────────────────────────────────────────────┘
```

### Implementation

| Component | Detail |
|-----------|--------|
| **Trigger** | Flask backend POSTs JSON after orchestrator completes |
| **Payload** | Session JSON: pet profile, triage tier, symptoms, agent outputs, language |
| **Guard** | Only fires if `N8N_WEBHOOK_URL` env var is set; otherwise silently skipped |
| **Threading** | Non-blocking (fires in a background thread so it doesn't slow the response) |

### POC Status

The webhook code is **implemented** in `api_server.py`. For the POC, it is **optional** — the app runs fully without any webhook configured. To enable it, set `N8N_WEBHOOK_URL` in `.env` to any URL (n8n, Slack incoming webhook, Zapier, custom endpoint).

For production, this layer would be expanded to support multiple event types (emergency alert, clinic summary delivery, appointment confirmation, analytics logging).

---

## Data Layer

| Component | Technology | Where It Runs | Purpose |
|-----------|-----------|--------------|---------|
| **Session Store (active)** | Python `dict` (in-memory) | Inside Flask process | Active intake sessions (1 hr TTL) |
| **Session Store (completed)** | Python `dict` (in-memory) | Inside Flask process | Completed triage sessions for PDF download (24 hr TTL) |
| **Session Cleanup** | Background thread (10 min interval) | Inside Flask process | Periodic expiry of stale sessions |
| **Clinic Rules** | `backend/data/clinic_rules.json` | Loaded at startup | Triage rules, routing maps, providers |
| **Red Flags** | `backend/data/red_flags.json` | Loaded at startup | 50+ emergency trigger terms |
| **Mock Schedule** | `backend/data/available_slots.json` | Loaded at startup | Simulated appointment slots |
| **Client Storage** | Browser `localStorage` | User's browser | Pet profiles, symptom history, consent, onboarding state |
| **Logging** | Python `logging` → `backend/logs/` | File + console | API requests, agent trace, errors |

### Design References (not used at runtime)

These were consulted for domain context when curating the operational JSON files above. They are **not** loaded or called by the system.

| Source | URL | How We Used It |
|--------|-----|----------------|
| HuggingFace Pet Health Dataset | [karenwky/pet-health-symptoms-dataset](https://huggingface.co/datasets/karenwky/pet-health-symptoms-dataset) | Symptom taxonomy / category ideas |
| ASPCA AnTox | [aspcapro.org/antox](https://www.aspcapro.org/antox) | Red-flag phrasing in `red_flags.json` |
| Vet-AI Symptom Checker | [vet-ai.com/symptomchecker](https://www.vet-ai.com/symptomchecker) | Triage workflow design inspiration |
| SAVSNET / PetBERT | [github.com/SAVSNET/PetBERT](https://github.com/SAVSNET/PetBERT) | NLP / coding patterns reference |

---

## Infrastructure & Deployment

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Container** | Docker (single container) | Bundles Python + app + frontend |
| **Cloud** | **Render (recommended)** / Railway (free tier) | Zero-cost POC hosting; Render is the smart bet (GitHub auto-deploy, HTTPS, minimal config). |
| **DNS/SSL** | Provided by Render / Railway | HTTPS by default |
| **CI/CD** | GitHub → Render auto-deploy | Push to `main` branch → auto-redeploy |
| **Version Control** | Git + GitHub | Source code on `main` branch |
| **Start Scripts** | `start.sh` / `start.ps1` | One-click local setup |
| **Monitoring** | `/api/health` endpoint | Basic health check |

### Deployment Options

| Option | Cost | Difficulty | Best For |
|--------|------|-----------|----------|
| **Local Python** | Free | Easy | Development, debugging |
| **Local Docker** | Free | Easy | Testing prod-like setup |
| **Render (free)** | $0/mo | Easy | **Recommended for POC** — live demo, sharing |
| **Render (paid)** | $7/mo | Easy | No cold starts |
| **Railway** | $5/mo | Easy | Alternative to Render |
| **AWS/GCP/Azure** | Variable | Medium | Production deployment |

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions.

---

## Python Dependencies

| Package | Purpose | Used By |
|---------|---------|---------|
| `flask` | Web server, REST API, static serving, HTTP Basic Auth | api_server.py |
| `flask-limiter` | Per-endpoint rate limiting (10/min session start, 20/min chat, 5/min voice) | api_server.py |
| `python-dotenv` | Load `.env` file into environment | api_server.py |
| `openai` | GPT-4o-mini, Whisper STT, `tts-1-hd` TTS, Vision, guardrail classifier | Intake, Triage, Guidance, Voice, Photo, guardrails |
| `langsmith` | LLM tracing + guardrail audit via `@traceable` and `wrap_openai` | orchestrator, guardrails |
| `requests` | HTTP client for webhook POST | api_server.py (webhook) |
| `fpdf2` | PDF generation for triage summary export | api_server.py (summary endpoint) |
| `gunicorn` | Production WSGI server (multi-worker) | Cloud deployment (Render, Docker) |

---

## Security & Privacy

| Concern | Approach |
|---------|----------|
| **Authentication** | HTTP Basic Auth via environment variables (`AUTH_ENABLED`, `AUTH_USERNAME`, `AUTH_PASSWORD`). Credentials never hardcoded. Health check and static assets exempted. |
| **Rate Limiting** | `flask-limiter`: 10/min session start, 20/min chat, 5/min voice, 15/min summary/PDF, 5/min photo, 3/min Twilio call. Closes VULN-01, VULN-02, VULN-06. |
| **Content-Safety Guardrails** | Two-stage pipeline: Stage 1 regex (8 categories, 181 tests, 7 languages, 0ms), Stage 2 LLM semantic classifier (GPT-4o-mini, ~300-500ms, prod default on via `GUARDRAIL_LLM_ENABLED=true`). Every Stage 2 decision traced in LangSmith. |
| **Input Validation** | `MAX_MESSAGE_LENGTH=2,000` chars enforced before LLM call. Anatomical plausibility check in Intake Agent rejects impossible species/symptom combinations. |
| **Output Sanitization** | `_escape_pet_profile()` HTML-encodes all user-supplied fields (`pet_name`, `breed`, `age`, `weight`) at summary API boundary. Summary endpoint scrubs `agent_outputs`, `evaluation_metrics`, `messages`. |
| **TTS Content Policy** | `_tts_policy_check()` blocks dosage language, prescription verbs, vet identity claims, named diagnoses, named antidotes from voice synthesis output (8 compiled regex patterns). |
| **API Keys** | `.env` file (gitignored); injected via `--env-file` in Docker or Render env vars |
| **Owner PII** | Session-only memory; no database, no persistent server-side storage |
| **Client-Side Storage** | Pet profiles in `localStorage` (user-controlled, clearable); no PII sent to server |
| **Medical Safety** | Non-diagnostic language enforced; Safety Gate blocks before routing; Intake plausibility check rejects nonsense symptoms |
| **Data Retention** | Anonymized logs only; no PHI stored anywhere. Sessions expire automatically (1hr active, 24hr completed). |
| **Transport** | HTTPS default on Render/Railway; HTTP locally |
| **Container Security** | `python:3.11-slim` base; no root processes; minimal attack surface |

## External API Integrations

| API | Purpose | Called From | Cost |
|-----|---------|-------------|------|
| **OpenAI GPT-4o-mini** | Intake, Triage, Guidance reasoning | Backend (agents) | ~$0.01/session |
| **OpenAI Whisper** | Voice transcription (Tier 2) | Backend (`/api/voice/transcribe`) | $0.006/min |
| **OpenAI TTS (`tts-1-hd`)** | Voice synthesis (Tier 2) — HD model, natural pacing | Backend (`/api/voice/synthesize`) | $15/1M chars |
| **OpenAI Vision** | Photo symptom analysis | Backend (`/api/photo/analyze`) | ~$0.002/photo |
| **Google Places API (New)** | Nearby vet clinic search | Frontend (client-side) | Free tier ($200/mo credit) |
| **OpenStreetMap Nominatim** | Geocoding fallback (city → lat/lng) | Frontend (client-side) | Free |

---

## Future Integrations (Post-POC)

| Integration | Technology | Effort | Impact |
|-------------|-----------|--------|--------|
| Clinic Scheduling API | REST / FHIR | Medium | Real-time booking |
| EMR/CRM | HL7 FHIR / proprietary | High | Patient record handoff |
| SMS/Email Notifications | Twilio / SendGrid | Low | Appointment confirmations |
| Persistent Sessions | Redis / PostgreSQL | Low | Sessions survive restarts |
| Production Server | Gunicorn + Nginx | Low | Multi-worker, production-grade |
| Formal orchestration | LangGraph (optional) | Medium | Explicit graph, checkpointing; same flow as current orchestrator. **Not Google ADK** (Vertex-centric). |
| Mobile App | React Native / Flutter | High | Native mobile experience |
| Analytics | PostHog / Mixpanel | Low | Usage + triage accuracy tracking |
