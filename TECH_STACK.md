# PetCare Triage & Smart Booking Agent -- Technology Stack

**Author:** Syed Ali Turab
**Date:** March 1, 2026

---

## What This Is Built On

The PetCare Agent is a **monolithic Python/Flask application** that bundles the frontend, backend API, orchestrator, and all 7 sub-agents into a **single deployable unit**. It runs inside a **single Docker container** (or directly via Python) and communicates with external LLM APIs (OpenAI / Anthropic) for AI reasoning.

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
        │  ├─ GPT-4.1 / GPT-4.1-mini  │
        │  ├─ Whisper (STT)            │
        │  ├─ TTS (text-to-speech)     │
        │  └─ Realtime API (Tier 3)    │
        │                              │
        │  Anthropic API               │
        │  └─ Claude 3.5+             │
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
   ├── IntakeAgent.process()          ← LLM call (OpenAI/Anthropic)
   ├── SafetyGateAgent.process()      ← Local rule-based (no API call)
   ├── ConfidenceGateAgent.process()  ← Local rule-based (no API call)
   ├── TriageAgent.process()          ← LLM call (OpenAI/Anthropic)
   ├── RoutingAgent.process()         ← Local rule-based (no API call)
   ├── SchedulingAgent.process()      ← Local rule-based (no API call)
   └── GuidanceSummaryAgent.process() ← LLM call (OpenAI/Anthropic)
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
├── Python packages: flask, openai, anthropic, langchain, pydantic (~200MB)
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
EXPOSE 5002                              # 5. Declare the port
CMD ["python", "backend/api_server.py"]  # 6. Start Flask server
```

The build is **deterministic**: same code + same requirements.txt = same image every time. No compiled assets or build steps needed (frontend is vanilla HTML/CSS/JS).

---

## Core Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Language** | Python | 3.10+ (3.11 in Docker) | All server-side logic, agent implementations |
| **Web Framework** | Flask | latest | REST API, static file serving, session management |
| **Frontend** | HTML5 / CSS3 / JavaScript (ES6+) | -- | Chat UI, voice controls, responsive design |
| **Containerization** | Docker | latest | Reproducible builds, single-container deployment |
| **Process Model** | Single-process, single-threaded | -- | Flask dev server (use Gunicorn for production) |

---

## AI / LLM Layer

| Component | Technology | Pricing | Used By |
|-----------|-----------|---------|---------|
| **Primary LLM** | OpenAI GPT-4.1-mini | ~$0.40/1M input, $1.60/1M output | Intake (A), Triage (D), Guidance (G) |
| **Upgrade LLM** | OpenAI GPT-4.1 | ~$2/1M input, $8/1M output | Complex triage cases |
| **Alternative** | Anthropic Claude 3.5 Sonnet | ~$3/1M input, $15/1M output | Fallback; strong safety reasoning |
| **Framework** | LangChain + LangChain-OpenAI | -- | Prompt templating, structured output |
| **Tracing** | LangSmith (optional) | Free tier | LLM call tracing, prompt debugging |

### Cost Per Intake Session (Estimated)

| Component | Tokens | Cost |
|-----------|--------|------|
| Intake Agent (1-3 LLM calls) | ~2,000 tokens | ~$0.004 |
| Triage Agent (1 LLM call) | ~1,000 tokens | ~$0.002 |
| Guidance Agent (1 LLM call) | ~1,500 tokens | ~$0.003 |
| Voice Tier 2 (if used) | 1 min audio | ~$0.02 |
| **Total per session** | | **~$0.01-0.03** |

---

## Multilingual Support

The system supports **7 languages** out of the box. The user selects their language from a dropdown in the header, and the entire experience -- UI, chat, voice input, and voice output -- switches to that language.

### Supported Languages

| Language | Code | Script | Direction | Whisper | Web Speech API | GPT-4.1 | TTS |
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
| GPT-4.1 responses | Same token cost | Multilingual is native |
| Whisper STT | Same per-minute cost | All languages supported |
| OpenAI TTS | Same per-character cost | Auto-detects language |
| Browser voice | Free | Language via BCP-47 tag |

---

## Voice Layer

Three tiers of voice interaction:

| Feature | Tier 1: Browser Native | Tier 2: Whisper + TTS | Tier 3: Realtime API |
|---------|----------------------|----------------------|---------------------|
| **Cost** | Free | ~$0.02/session | ~$0.50-1.00/session |
| **Latency** | ~100ms (client-side) | ~1-2s (API round-trip) | <500ms (WebSocket) |
| **Quality** | Varies by browser | High (Whisper) | Highest (native) |
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

## Workflow Automation Layer (n8n)

n8n is the **actions layer** -- it handles everything that happens *after* the agent pipeline finishes. The agent logic stays in Python; n8n handles the downstream integrations with zero coupling.

### What n8n Does

```
PetCare Agent completes intake
        │
        │  POST webhook (JSON payload)
        ▼
┌─────────────────────────────────────────────┐
│               n8n Workflow Engine            │
│                                             │
│  Workflow 1: Emergency Alert                │
│  ├─ Slack → #emergency channel              │
│  └─ Email → on-call vet                     │
│                                             │
│  Workflow 2: Clinic Summary Delivery        │
│  ├─ Email → clinic inbox (formatted HTML)   │
│  └─ Google Sheets → append intake row       │
│                                             │
│  Workflow 3: Appointment Confirmation       │
│  ├─ Email → pet owner                       │
│  └─ Google Calendar → create event (mock)   │
│                                             │
│  Workflow 4: Analytics Logger               │
│  └─ Google Sheets → session metrics         │
│     (triage tier, confidence, latency, lang) │
│                                             │
│  Workflow 5: Follow-Up Reminder (stretch)   │
│  └─ Email → pet owner (24hr delayed)        │
└─────────────────────────────────────────────┘
```

### n8n vs Alternatives

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **n8n (self-hosted)** | Free, open-source, visual workflow builder, 400+ integrations, runs in Docker | Needs a second container | **Chosen** |
| **n8n Cloud** | Same as above + no Docker needed | 300 exec/mo free tier | Good fallback |
| **Zapier** | Easy to use | Expensive ($20/mo+), proprietary | Too expensive for POC |
| **Custom Python code** | No dependencies | Tightly couples agent logic to email/Slack/Sheets code | Bad separation |
| **AWS Step Functions** | Enterprise-grade | Overkill, requires AWS account | Too complex |

### How It Connects

| Component | Detail |
|-----------|--------|
| **Trigger** | n8n Webhook node receives POST from Flask backend |
| **Payload** | Session JSON: pet profile, triage tier, symptoms, agent outputs, language |
| **Transport** | HTTP (localhost in Docker network, HTTPS in cloud) |
| **Backend change** | Add ~10 lines: `requests.post(N8N_WEBHOOK_URL, json=session_data)` after orchestrator completes |
| **n8n runs** | As a separate Docker container (via docker-compose) or n8n Cloud |

### Deployment

| Option | Setup | Cost |
|--------|-------|------|
| **docker-compose (recommended)** | `docker-compose up` runs petcare + n8n together | Free |
| **n8n Cloud** | Sign up → paste webhook URL into `.env` | Free (300 exec/mo) |

### n8n Credentials Needed (for workflows)

| Service | What to Set Up | Free Tier |
|---------|---------------|-----------|
| Gmail / SMTP | Email sending (clinic summary, confirmations) | Free |
| Slack | Incoming webhook for emergency alerts | Free |
| Google Sheets | API key for intake logging | Free |
| Google Calendar | API key for appointment events (mock) | Free |

---

## Data Layer

| Component | Technology | Where It Runs | Purpose |
|-----------|-----------|--------------|---------|
| **Session Store** | Python `dict` (in-memory) | Inside Flask process | Active intake sessions |
| **Clinic Rules** | `backend/data/clinic_rules.json` | Loaded at startup | Triage rules, routing maps, providers |
| **Red Flags** | `backend/data/red_flags.json` | Loaded at startup | 50+ emergency trigger terms |
| **Mock Schedule** | `backend/data/available_slots.json` | Loaded at startup | Simulated appointment slots |
| **Logging** | Python `logging` → `backend/logs/` | File + console | API requests, agent trace, errors |

### External Data Sources

| Source | URL | Used By |
|--------|-----|---------|
| HuggingFace Pet Health Dataset | [karenwky/pet-health-symptoms-dataset](https://huggingface.co/datasets/karenwky/pet-health-symptoms-dataset) | Intake (A), Triage (D) |
| ASPCA AnTox | [aspcapro.org/antox](https://www.aspcapro.org/antox) | Safety Gate (B) |
| Vet-AI Symptom Checker | [vet-ai.com/symptomchecker](https://www.vet-ai.com/symptomchecker) | Triage (D), Routing (E) |
| SAVSNET / PetBERT | [github.com/SAVSNET/PetBERT](https://github.com/SAVSNET/PetBERT) | NLP reference |

---

## Infrastructure & Deployment

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Container** | Docker (single container) | Bundles Python + app + frontend |
| **Cloud** | Render / Railway (free tier) | Zero-cost POC hosting |
| **DNS/SSL** | Provided by Render/Railway | HTTPS by default |
| **CI/CD** | GitHub → Render auto-deploy | Push to `PetCare_Syed` branch → auto-redeploy |
| **Version Control** | Git + GitHub | Source code on `PetCare_Syed` branch |
| **Start Scripts** | `start.sh` / `start.ps1` | One-click local setup |
| **Monitoring** | `/api/health` endpoint | Basic health check |

### Deployment Options

| Option | Cost | Difficulty | Best For |
|--------|------|-----------|----------|
| **Local Python** | Free | Easy | Development, debugging |
| **Local Docker** | Free | Easy | Testing prod-like setup |
| **Render (free)** | $0/mo | Easy | Live demo, sharing |
| **Render (paid)** | $7/mo | Easy | No cold starts |
| **Railway** | $5/mo | Easy | Alternative to Render |
| **AWS/GCP/Azure** | Variable | Medium | Production deployment |

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions.

---

## Python Dependencies

| Package | Purpose | Used By |
|---------|---------|---------|
| `flask` | Web server, REST API, static serving | api_server.py |
| `python-dotenv` | Load `.env` file into environment | api_server.py |
| `pydantic` | JSON schema validation, data models | All agents |
| `openai` | GPT-4.1, Whisper STT, TTS, Realtime API | Intake, Triage, Guidance, Voice |
| `anthropic` | Claude API client | Configurable fallback LLM |
| `langchain` | LLM abstraction, prompt templates | Agent prompting |
| `langchain-openai` | LangChain ↔ OpenAI bridge | Agent prompting |
| `langchain-anthropic` | LangChain ↔ Anthropic bridge | Agent prompting |
| `gunicorn` | Production WSGI server | Cloud deployment |
| `streamlit` | Quick prototyping UI (from main branch) | Optional |

---

## Security & Privacy

| Concern | Approach |
|---------|----------|
| **API Keys** | `.env` file (gitignored); injected via `--env-file` in Docker |
| **Owner PII** | Session-only memory; no database, no persistent storage |
| **Medical Safety** | Non-diagnostic language enforced; Safety Gate blocks before routing |
| **Data Retention** | Anonymized logs only; no PHI stored anywhere |
| **Transport** | HTTPS default on Render/Railway; HTTP locally |
| **Container Security** | `python:3.11-slim` base; no root processes; minimal attack surface |

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
