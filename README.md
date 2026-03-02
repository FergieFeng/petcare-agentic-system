# 🐾 PetCare Agentic System

**Authors:** Syed Ali Turab & Fergie Feng | **Team:** Broadview
**Date:** March 1, 2026

AI-powered Veterinary Triage & Smart Booking System
A safety-first, multi-agent architecture designed to assist veterinary clinics with structured symptom intake, urgency triage, intelligent routing, and appointment booking — built as part of the MMAI 891 Final Project at Queen's University.

---

## 🚀 Overview

PetCare Agentic System is an AI receptionist framework built to reduce call overload in veterinary clinics by:

- Collecting structured symptom information via chat or voice (7 languages)
- Safely triaging urgency levels with deterministic red-flag detection
- Routing cases to the correct service line or veterinarian
- Booking appointments intelligently from clinic schedule
- Generating clinic-ready structured summaries (JSON)
- Providing conservative waiting guidance to pet owners
- Triggering post-intake automations via n8n (email, Slack, Sheets)

The system is designed with **layered responsibility separation**, **safety constraints**, and **extensibility** in mind.

---

## 🎯 Problem Statement

Veterinary clinics often face:

- **High call volumes** — front desk overwhelmed during peak hours
- **Incomplete symptom descriptions** — owners omit critical details
- **Mis-booked appointments** — wrong provider, wrong urgency, wrong slot
- **Repeated clarification calls** — staff calling back to collect missing info
- **Inconsistent triage** — urgency varies by who answers the phone

This system addresses those issues through structured AI-assisted intake and routing with a multi-agent architecture.

---

## 🧠 System Architecture

### System Architecture (Full Stack)

```mermaid
graph TD
    BROWSER["User Browser — Chat UI · Voice · 7 Languages"]

    BROWSER -->|HTTP| FLASK["Flask API Server — Port 5002"]
    FLASK --> ORCH["Orchestrator"]
    FLASK --> SESSION["Session Store — In-Memory"]
    FLASK -->|webhook| N8N_IN["n8n Webhook Receiver"]

    ORCH --> A["A · Intake — LLM"]
    ORCH --> B["B · Safety Gate — Rules"]
    ORCH --> CC["C · Confidence — Rules"]
    ORCH --> D["D · Triage — LLM"]
    ORCH --> E["E · Routing — Rules"]
    ORCH --> FF["F · Scheduling — Rules"]
    ORCH --> GA["G · Guidance — LLM"]

    A -->|API call| OPENAI["OpenAI API — GPT-4.1 · Whisper · TTS"]
    D -->|API call| OPENAI
    GA -->|API call| OPENAI
    GA -.->|fallback| CLAUDE["Anthropic Claude 3.5"]

    B --> DATA["JSON Config — clinic_rules · red_flags · slots"]
    CC --> DATA
    E --> DATA
    FF --> DATA

    N8N_IN --> W1["n8n: Emergency Alert"]
    N8N_IN --> W2["n8n: Clinic Summary Email"]
    N8N_IN --> W3["n8n: Appt Confirmation"]
    N8N_IN --> W4["n8n: Analytics Logger"]

    W1 --> SVC["Slack · Gmail · Google Sheets"]
    W2 --> SVC
    W3 --> SVC
    W4 --> SVC

    style A fill:#dc2626,color:#fff
    style D fill:#dc2626,color:#fff
    style GA fill:#dc2626,color:#fff
    style B fill:#16a34a,color:#fff
    style CC fill:#16a34a,color:#fff
    style E fill:#16a34a,color:#fff
    style FF fill:#16a34a,color:#fff
    style N8N_IN fill:#ea580c,color:#fff
    style W1 fill:#ea580c,color:#fff
    style W2 fill:#ea580c,color:#fff
    style W3 fill:#ea580c,color:#fff
    style W4 fill:#ea580c,color:#fff
```

**Color key:** 🔴 Red = LLM-powered agent (API call) · 🟢 Green = Rule-based agent (zero cost) · 🟠 Orange = n8n workflow

---

### 🔄 Agent Pipeline Flow

```mermaid
graph TD
    START(("Pet Owner sends message"))

    START --> A["A · Intake Agent — LLM"]
    A --> B["B · Safety Gate — Rules"]
    B --> B_Q{"Emergency?"}
    B_Q -- YES --> EM["EMERGENCY — Escalate now"]
    B_Q -- NO --> CC["C · Confidence Gate — Rules"]
    CC --> C_Q{"Fields complete?"}
    C_Q -- NO --> LOOP["Clarify with user"]
    LOOP --> A
    C_Q -- YES --> D["D · Triage Agent — LLM"]
    D --> E["E · Routing Agent — Rules"]
    E --> FF["F · Scheduling Agent — Rules"]
    FF --> GA["G · Guidance Agent — LLM"]
    GA --> OUT1["Owner: Urgency + Guidance"]
    GA --> OUT2["Clinic: Structured JSON"]

    style A fill:#dc2626,color:#fff
    style D fill:#dc2626,color:#fff
    style GA fill:#dc2626,color:#fff
    style B fill:#16a34a,color:#fff
    style CC fill:#16a34a,color:#fff
    style E fill:#16a34a,color:#fff
    style FF fill:#16a34a,color:#fff
    style EM fill:#991b1b,color:#fff
    style LOOP fill:#f59e0b,color:#000
```

**Legend:** 🔴 Red = LLM-powered (API call, ~$0.002 each) · 🟢 Green = Rule-based (local, zero cost)

---

### 🎤 Voice Architecture

```mermaid
graph TD
    MIC["User Microphone"]

    MIC -->|Tier 1| SR["Browser SpeechRecognition — Free"]
    MIC -->|Tier 2| REC["MediaRecorder — audio/webm"]
    MIC -->|Tier 3| RT["OpenAI Realtime API — WebSocket"]

    SR --> TXT["Transcribed Text"]
    REC -->|POST /api/voice/transcribe| WHISPER["Whisper API — $0.006/min"]
    WHISPER --> TXT

    TXT --> PIPE["Agent Pipeline — 7 Agents"]

    PIPE --> RESP["Agent Response Text"]

    RESP -->|Tier 1| SYNTH["Browser SpeechSynthesis — Free"]
    RESP -->|Tier 2| TTS["OpenAI TTS — $15/1M chars"]

    SYNTH --> SPK["Speaker Output"]
    TTS --> SPK

    RT <-->|bidirectional| SPK_RT["Speaker — sub-500ms"]

    style SR fill:#16a34a,color:#fff
    style SYNTH fill:#16a34a,color:#fff
    style WHISPER fill:#2563eb,color:#fff
    style TTS fill:#2563eb,color:#fff
    style RT fill:#7c3aed,color:#fff
    style SPK_RT fill:#7c3aed,color:#fff
```

**Color key:** 🟢 Green = Tier 1 (free, browser-native) · 🔵 Blue = Tier 2 (OpenAI Whisper + TTS) · 🟣 Purple = Tier 3 (Realtime API, stretch)

---

## 🤖 Core Multi-Agent Layer

The PetCare Agent uses a **7-sub-agent architecture** coordinated by a central **Orchestrator Agent**:

| # | Agent | Type | Responsibility |
|---|-------|------|---------------|
| A | **Intake Agent** | 🔴 LLM | Collect pet profile + chief complaint + timeline; ask adaptive follow-ups by symptom area |
| B | **Safety Gate Agent** | 🟢 Rules | Detect emergency red flags → immediate escalation messaging |
| C | **Confidence Gate Agent** | 🟢 Rules | Verify required fields and confidence; route to clarification or receptionist review |
| D | **Triage Agent** | 🔴 LLM | Assign urgency tier (Emergency / Same-day / Soon / Routine) with rationale + confidence |
| E | **Routing Agent** | 🟢 Rules | Classify symptom category → appointment type / provider pool |
| F | **Scheduling Agent** | 🟢 Rules | Propose available slots or generate booking request payload |
| G | **Guidance & Summary Agent** | 🔴 LLM | Generate owner "do/don't" guidance + structured clinic-ready intake summary |

Only 3 of 7 agents make LLM API calls (~$0.01/session). The other 4 run locally as deterministic rules with zero cost.

Agents operate under role-based data permissions to maintain safety boundaries. See [docs/architecture/agents.md](docs/architecture/agents.md) for full I/O contracts and data access policy.

---

## 🗄 Data Layer

| Data Store | Purpose | Used By |
|-----------|---------|---------|
| `backend/data/clinic_rules.json` | Triage rules, routing maps, provider specialties | Triage (D), Routing (E) |
| `backend/data/red_flags.json` | 50+ emergency trigger phrases | Safety Gate (B) |
| `backend/data/available_slots.json` | Mock clinic schedule (30-min slots) | Scheduling (F) |
| In-memory session | Active intake records, appointments | All agents via Orchestrator |

See [docs/architecture/data_model.md](docs/architecture/data_model.md) for full schemas.

---

## 🛡 Safety-First Design Principles

> Core innovation lies in safety-grounded triage and structured routing — not just conversational AI.

This system is **not merely a chatbot**. It is a safety-constrained, rule-grounded, modular multi-agent orchestration framework.

- **No medical diagnosis generation** — never provides diagnoses or prescriptions
- **Deterministic safety layer** — red-flag detection runs as rules before any AI reasoning
- **Rule-grounded urgency classification** — triage maps to clinic-approved rules
- **Red-flag symptom escalation** — 50+ curated emergency triggers with mandatory escalation
- **Structured confirmation** — critical fields verified by Confidence Gate before triage
- **Separation between triage and booking** — urgency classification isolated from scheduling
- **Minimal PII storage** — session-only memory, no persistent owner data
- **Conservative defaults** — when uncertain, escalate rather than under-triage

---

## 🎤 Voice Support

Three tiers of voice interaction for hands-free intake (ideal for pet owners holding a distressed pet):

| Tier | Technology | Cost | Latency | Feel |
|------|-----------|------|---------|------|
| **Tier 1** | Browser Web Speech API | Free | ~100ms | Walkie-talkie |
| **Tier 2** | OpenAI Whisper + TTS | ~$0.02/session | ~1-2s | Walkie-talkie |
| **Tier 3** | OpenAI Realtime API | ~$0.50/session | <500ms | Natural phone call |

Voice is an **opt-in I/O wrapper** — it does NOT alter business logic or agent decisions.

Voice mode requires:
- Critical symptom confirmation via voice
- Noise-handling fallback (text if low confidence)
- Red-flag double confirmation before escalation

See [TECH_STACK.md](TECH_STACK.md) for full voice safety requirements and testing metrics.

---

## 🌐 Multilingual Support

The system supports **7 languages** with full UI translation, RTL support, and multilingual voice:

| Language | Flag | Direction | Voice (STT/TTS) |
|----------|------|-----------|-----------------|
| English | 🇬🇧 | LTR | Full |
| French | 🇫🇷 | LTR | Full |
| Chinese (Mandarin) | 🇨🇳 | LTR | Full |
| Arabic | 🇸🇦 | **RTL** | Full |
| Spanish | 🇪🇸 | LTR | Full |
| Hindi | 🇮🇳 | LTR | Full |
| Urdu | 🇵🇰 | **RTL** | Full |

- Arabic and Urdu automatically flip the layout to right-to-left (RTL)
- Clinic-facing summaries are always generated in English
- Language can be changed mid-conversation
- Set language via URL parameter: `?lang=fr`

---

## 🏷 Technology Stack

| Layer | Technology | Cost |
|-------|-----------|------|
| **Frontend** | HTML5 / CSS3 / JavaScript (ES6+) | Free |
| **Backend** | Python 3.11 + Flask | Free |
| **LLM (Primary)** | OpenAI GPT-4.1-mini | ~$0.01/session |
| **LLM (Fallback)** | Anthropic Claude 3.5 Sonnet | ~$0.02/session |
| **Voice STT** | OpenAI Whisper | $0.006/min |
| **Voice TTS** | OpenAI TTS (tts-1) | $15/1M chars |
| **LLM Framework** | LangChain + LangChain-OpenAI | Free |
| **Workflow Automation** | n8n (self-hosted or cloud) | Free |
| **Containerization** | Docker + docker-compose | Free |
| **Hosting** | **Render (recommended)** / Railway (free tier) | $0/mo — Render recommended for POC (GitHub auto-deploy, HTTPS). |
| **Languages** | 7 (EN, FR, ZH, AR, ES, HI, UR) | Free |
| **Version Control** | Git + GitHub (`PetCare_Syed` branch) | Free |

See [TECH_STACK.md](TECH_STACK.md) for full details, runtime architecture, and agent deployment model.

---

## 📊 Data Sources

### Symptom & Triage Knowledge

| Source | Type | Usage |
|--------|------|-------|
| [HuggingFace: pet-health-symptoms-dataset](https://huggingface.co/datasets/karenwky/pet-health-symptoms-dataset) | Open dataset (2,000 samples) | Symptom classification |
| [Vet-AI Symptom Checker](https://www.vet-ai.com/symptomchecker) | 165 triage algorithms | Triage logic patterns |
| [SAVSNET / PetBERT](https://github.com/SAVSNET/PetBERT) | 500M+ words, 5.1M records | Veterinary NLP reference |

### Safety & Toxicology

| Source | Type | Usage |
|--------|------|-------|
| [ASPCA Animal Poison Control](https://www.aspcapro.org/antox) | 1M+ cases | Red-flag rules for toxin ingestion |
| Veterinary emergency textbooks | Clinical reference | Emergency red-flag definitions |

### Clinic Operations (Synthetic)

| Source | Type | Usage |
|--------|------|-------|
| `backend/data/clinic_rules.json` | Synthetic config | Triage rules, routing maps |
| `backend/data/red_flags.json` | Curated list (50+ entries) | Emergency triggers |
| `backend/data/available_slots.json` | Mock data | Appointment booking POC |

All POC data is synthetic. No real patient/pet health information (PHI) is used.

---

## 🧪 MVP Demo Flow

1. Owner describes symptoms via chat (text or voice, any of 7 languages)
2. **Intake Agent** asks structured follow-up questions
3. **Safety Gate** checks for emergency red flags
4. **Confidence Gate** verifies data completeness
5. **Triage Agent** classifies urgency tier
6. **Routing Agent** selects appointment type + provider pool
7. **Scheduling Agent** proposes available slots
8. **Guidance Agent** generates owner do/don't guidance + clinic summary
9. **n8n** triggers post-intake automations (email, Slack, Sheets)

---

## ⚠️ Current Status

> **This project has NOT been tested yet.** All code, agents, and endpoints are scaffolded and documented but have not been run or validated end-to-end. Expect breaking issues on first run. Testing and iteration is the immediate next step.

| Area | Status |
|------|--------|
| Architecture & documentation | ✅ Complete |
| Agent implementations (A–G) | ✅ Scaffolded (untested) |
| Orchestrator | ✅ Scaffolded (untested) |
| Flask API server | ✅ Scaffolded (untested) |
| Frontend (chat + voice + multilingual) | ✅ Scaffolded (untested) |
| Docker / docker-compose | ✅ Written (untested) |
| n8n workflows | ✅ Documented (not configured) |
| End-to-end integration testing | ❌ Not started |
| Unit / agent-level testing | ❌ Not started |
| Deployment to cloud (Render recommended) | ❌ Not started |

---

## 📋 Next Steps (update as we knock them off)

**Due:** March 22, 2026 · **Target build complete:** March 10–11, 2026 · *Today: March 2, 2026*

| # | Step | Status |
|---|------|--------|
| 1 | Wire Orchestrator into API (`api_server.py` → `handle_message()`) | ⬜ |
| 2 | Unblock Intake so pipeline can complete (set `intake_complete: True` when species + chief complaint present — rule or LLM) | ⬜ |
| 3 | Smoke test: run backend locally, send one message end-to-end, confirm triage + guidance response | ⬜ |
| 4 | Validate Scenario 1 (emergency) and Scenario 3 (toxin) — Safety Gate + emergency path | ⬜ |
| 5 | Validate Scenario 2 (routine skin) and Scenario 4 (ambiguous → clarify) — full pipeline + confidence gate | ⬜ |
| 6 | Add language to Intake/Triage/Guidance prompts; verify voice (Tier 1/2) | ⬜ |
| 7 | Deploy to **Render** (recommended); add env vars, confirm live URL | ⬜ |
| 8 | Optional: n8n webhooks (Emergency Alert + Clinic Summary) | ⬜ |
| 9 | Evaluation: 20+ scenarios, metrics; document 1 strong + 1 failure case | ⬜ |
| 10 | Report + 10–15 min demo video; final README polish | ⬜ |

Full detail: [NEXT_STEPS.md](NEXT_STEPS.md).

---

## 🏗 Development Phases

| Phase | Focus | Status |
|-------|-------|--------|
| **Phase 1** | Core text-based triage (7 agents + orchestrator) | 📝 Scaffolded (untested) |
| **Phase 2** | Voice support (3 tiers) + multilingual (7 languages) | 📝 Scaffolded (untested) |
| **Phase 3** | Docker containerization + deployment pipeline | 📝 Written (untested) |
| **Phase 4** | n8n workflow automation (actions layer) | 📝 Documented (not configured) |
| **Phase 5** | Evaluation & testing | ❌ Not started |
| **Phase 6** | Report, video & polish | 📋 Planned |

See [PROJECT_PLAN.md](PROJECT_PLAN.md) for full sprint-by-sprint plan with risk register.

---

## 🚀 Quick Start (Docker — Recommended)

Requires only [Git](https://git-scm.com/) and [Docker Desktop](https://www.docker.com/products/docker-desktop/).

### macOS / Linux

```bash
git clone https://github.com/FergieFeng/petcare-agentic-system.git
cd petcare-agentic-system
git checkout PetCare_Syed
./start.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/FergieFeng/petcare-agentic-system.git
cd petcare-agentic-system
git checkout PetCare_Syed
powershell -ExecutionPolicy Bypass -File start.ps1
```

Open [http://localhost:5002](http://localhost:5002) in your browser.

> After someone pushes changes, run the same script again — it pulls and rebuilds automatically. API keys are saved locally.

### Docker Manual Build

```bash
docker build -t petcare-agent .
docker run -p 5002:5002 --env-file .env petcare-agent
```

---

## 🐍 Quick Start (Local Python)

```bash
git clone https://github.com/FergieFeng/petcare-agentic-system.git
cd petcare-agentic-system
git checkout PetCare_Syed

python -m venv .venv
source .venv/bin/activate        # macOS/Linux
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your API keys

cd backend
python api_server.py
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes (if using OpenAI) | OpenAI API key for GPT-4.1 |
| `ANTHROPIC_API_KEY` | Yes (if using Anthropic) | Anthropic API key for Claude |
| `DEFAULT_LLM_PROVIDER` | No | `openai` (default) or `anthropic` |
| `DEFAULT_LLM_MODEL` | No | Model name (default: `gpt-4.1-mini`) |
| `PORT` | No | Server port (default: `5002`) |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `N8N_WEBHOOK_URL` | No | n8n webhook URL (auto-set by docker-compose) |

---

## 📁 Project Structure

```
├── frontend/                    # Frontend files
│   ├── index.html               # Main HTML (intake chat UI)
│   ├── js/app.js                # Client-side logic (voice, multilingual)
│   └── styles/main.css          # Styles (RTL support)
├── backend/                     # Backend files
│   ├── api_server.py            # Flask API server
│   ├── orchestrator.py          # Orchestrator (coordinates sub-agents)
│   ├── agents/                  # Sub-agent implementations (A-G)
│   ├── data/                    # Clinic rules, red flags, mock schedule
│   └── logs/                    # Runtime logs
├── docs/                        # Documentation
│   ├── architecture/            # System-level design docs
│   ├── agent_specs/             # Per-agent design work packages (intake, triage, etc.)
│   └── original_main/           # Preserved docs from main branch (Fergie's design)
├── Dockerfile                   # Single-container deployment
├── docker-compose.yml           # Multi-container: petcare + n8n
├── start.sh / start.ps1         # One-click Docker start
├── requirements.txt             # Python dependencies
├── PROJECT_PLAN.md              # Project plan and timeline
├── TECH_STACK.md                # Full technology stack
├── DEPLOYMENT_GUIDE.md          # Step-by-step deployment
├── technical_report.md          # MMAI 891 report template
└── .env.example                 # Environment variable template
```

---

## 📈 Success Metrics (MVP)

| Metric | Target |
|--------|--------|
| Triage tier agreement with clinic staff | ≥ 80% |
| Routing accuracy (correct appointment type) | ≥ 80% |
| Intake completeness (required fields captured) | ≥ 90% |
| Receptionist intake time reduction | 30%+ |
| Re-booking / mis-booking reduction | 20%+ |
| Red flag detection rate | 100% |

---

## 📌 Design Philosophy

> Core innovation lies in safety-grounded triage and structured routing — not just conversational AI.

The system is built to be:

- **Modular** — agents can be extended or replaced independently
- **Extensible** — voice, telephony, and new agents added without altering triage core
- **Safety-aligned** — deterministic safety layer + conservative defaults
- **Clinically practical** — structured outputs for real clinic workflows

---

## 📄 Documentation

| Document | Description |
|----------|-------------|
| [TECH_STACK.md](TECH_STACK.md) | Full technology stack, runtime architecture, how agents are deployed |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Step-by-step deployment (local Python, Docker, Render, Railway) |
| [docs/architecture/system_overview.md](docs/architecture/system_overview.md) | Overall architecture and design rationale |
| [docs/architecture/agents.md](docs/architecture/agents.md) | Agent responsibilities, I/O contracts, data access policy, design decisions |
| [docs/architecture/orchestrator.md](docs/architecture/orchestrator.md) | Orchestration logic, rules, and decision ownership |
| [docs/architecture/data_model.md](docs/architecture/data_model.md) | Data schemas, field specs, access policy, privacy guidance |
| [docs/architecture/repo_structure.md](docs/architecture/repo_structure.md) | Repository layout and design rationale |
| [docs/test_scenarios.md](docs/test_scenarios.md) | 6 end-to-end test scenarios + validation checklist |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Full project changelog |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Sprint-by-sprint project plan |
| [NEXT_STEPS.md](NEXT_STEPS.md) | **Build order:** wire API → orchestrator, unblock Intake, smoke test, validate scenarios |
| [technical_report.md](technical_report.md) | Technical report (assignment deliverable) |

---

## 🔮 Future Extensions

- Insurance pre-authorization agent
- Follow-up care agent
- Vaccination reminder automation
- Telemedicine integration
- Analytics dashboard for clinic operations
- Formal orchestration (LangGraph — optional post-POC)

---

## 📄 License

Educational / MMAI 891 Final Project — Queen's University

---

## 🤝 Contribution

This project is structured for modular expansion. Contributions should preserve:

- Safety boundaries
- Agent responsibility isolation
- Rule-grounded triage design

---

## Data Sources

The PetCare agent draws triage knowledge, symptom data, and red-flag rules from the following sources:

### Symptom & Triage Knowledge

| Source | Type | Usage |
|--------|------|-------|
| [Hugging Face: pet-health-symptoms-dataset](https://huggingface.co/datasets/karenwky/pet-health-symptoms-dataset) | Open dataset (2,000 labeled samples) | Symptom classification training/validation -- covers skin irritations, digestive issues, parasites, ear infections, mobility problems |
| [Vet-AI Symptom Checker](https://www.vet-ai.com/symptomchecker) | Reference | Triage logic patterns -- 165 algorithms built by veterinarians, 4M+ questions processed |
| [SAVSNET / PetBERT](https://github.com/SAVSNET/PetBERT) | NLP model (500M+ words from 5.1M UK vet records) | Reference for veterinary NLP and disease coding patterns |

### Safety & Toxicology

| Source | Type | Usage |
|--------|------|-------|
| [ASPCA Animal Poison Control (AnTox)](https://www.aspcapro.org/antox) | Reference database (1M+ cases) | Red-flag rules for toxin ingestion -- top toxins, species-specific risks |
| [ASPCA Top Toxins 2024](https://www.aspcapro.org/resource/top-10-toxins-2024) | Published list | Prioritized toxin list for Safety Gate agent (OTC meds 16.5%, food/drink 16.1%, chocolate 13.6%, etc.) |
| Veterinary emergency textbooks | Clinical reference | Emergency red-flag definitions (GDV, urinary blockage, dyspnea, seizure, etc.) |

### Clinic Operations (Synthetic / Mock)

| Source | Type | Usage |
|--------|------|-------|
| `backend/data/clinic_rules.json` | Synthetic config | Triage rules, routing maps, provider specialties, species notes |
| `backend/data/red_flags.json` | Curated list (50+ entries) | Emergency red-flag triggers compiled from ASPCA + veterinary emergency guidelines |
| `backend/data/available_slots.json` | Mock data | Simulated clinic schedule for appointment booking POC |

### Data Strategy

- **POC phase:** All data is synthetic or publicly available. No real patient/pet health information (PHI) is used.
- **Future integration:** Clinic scheduling APIs, EMR/CRM systems, real-time appointment availability.
- **Privacy:** Session-only memory. No persistent storage of owner PII. Anonymized logs for evaluation only.

---

## Current Status

> **⚠️ This project has NOT been tested yet.** The code, agents, and endpoints are scaffolded and documented but have not been run or validated end-to-end. Expect breaking issues on first run. Testing and iteration is the immediate next step.

| Area | Status |
|------|--------|
| Architecture & documentation | ✅ Complete |
| Agent implementations (A–G) | ✅ Scaffolded (untested) |
| Orchestrator | ✅ Scaffolded (untested) |
| Flask API server | ✅ Scaffolded (untested) |
| Frontend (chat + voice + multilingual) | ✅ Scaffolded (untested) |
| Docker / docker-compose | ✅ Written (untested) |
| n8n workflows | ✅ Documented (not configured) |
| End-to-end integration testing | ❌ Not started |
| Unit / agent-level testing | ❌ Not started |
| Deployment to cloud (Render recommended) | ❌ Not started |

---

## Summary

This project demonstrates how a **multi-agent architecture with a central orchestrator** can deliver structured, safe, and explainable decision support for veterinary intake triage and appointment booking, while maintaining clear scope and academic rigor.

Built with safety-first agent architecture by **Team Broadview**.
