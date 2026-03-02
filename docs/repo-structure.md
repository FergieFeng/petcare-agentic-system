# Repository Structure

**Author:** Syed Ali Turab | **Date:** March 1, 2026

---

## 1. Purpose

This document defines the repository layout for the PetCare Agentic System. The structure supports:

- Flask-based API server with in-process agent orchestration
- Modular sub-agent design (7 agents + orchestrator)
- Static frontend served by Flask
- Docker containerization (single container + n8n via docker-compose)
- Documentation separated from implementation

---

## 2. Directory Overview

```
petcare-agentic-system/
│
├── README.md                       # Project overview, architecture diagrams, setup
├── PROJECT_PLAN.md                 # Development roadmap, phases, risk register
├── TECH_STACK.md                   # Full technology stack, deployment details
├── DEPLOYMENT_GUIDE.md             # Step-by-step deployment instructions
├── technical_report.md             # MMAI 891 assignment report template
│
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Single-container Docker build
├── docker-compose.yml              # Multi-container: petcare-agent + n8n
├── start.sh / start.ps1            # One-click Docker start scripts
│
├── backend/                        # Python backend
│   ├── api_server.py               # Flask app, REST endpoints, static serving
│   ├── orchestrator.py             # Agent orchestration, workflow control
│   ├── agents/                     # Sub-agent implementations
│   │   ├── intake_agent.py         # Agent A: symptom collection (LLM)
│   │   ├── safety_gate_agent.py    # Agent B: red-flag detection (Rules)
│   │   ├── confidence_gate.py      # Agent C: field validation (Rules)
│   │   ├── triage_agent.py         # Agent D: urgency classification (LLM)
│   │   ├── routing_agent.py        # Agent E: category → service line (Rules)
│   │   ├── scheduling_agent.py     # Agent F: slot matching (Rules)
│   │   └── guidance_summary.py     # Agent G: guidance + summary (LLM)
│   ├── data/                       # Static data (replaces database for POC)
│   │   ├── clinic_rules.json       # Triage rules, routing maps, providers
│   │   ├── red_flags.json          # 50+ emergency trigger phrases
│   │   └── available_slots.json    # Mock appointment schedule
│   └── logs/                       # Runtime logs
│
├── frontend/                       # Client-side UI (served by Flask)
│   ├── index.html                  # Chat interface, language selector, voice
│   ├── js/app.js                   # Chat logic, voice, multilingual, API calls
│   └── styles/main.css             # Responsive styling, RTL support
│
├── docs/                           # Documentation
│   ├── architecture.md             # System architecture
│   ├── agent-design.md             # Agent specs, I/O contracts, access policy
│   ├── data-model.md               # Data schemas, privacy guidance
│   ├── voice-extension.md          # Voice tiers, safety, testing
│   ├── workflow-use-cases.md       # Test scenarios, validation checklist
│   ├── repo-structure.md           # This file
│   └── changelog.md                # Project history
│
└── src/                            # Legacy prototype code (from initial setup)
    ├── agents/                     # Early agent stubs
    ├── orchestrator/               # Early orchestrator stubs
    ├── shared/                     # Config, LLM helpers
    └── ui/                         # Prototype UI module
```

---

## 3. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Flask over FastAPI** | Simpler for POC; serves static frontend directly |
| **Vanilla JS over React** | No build step, no npm, no framework complexity |
| **JSON files over database** | Sufficient for POC; easy to inspect and edit |
| **Custom orchestrator over LangGraph** | Simpler, debuggable, meets assignment requirements |
| **Single Docker container** | All-in-one deployment; n8n runs as separate container |
| **Docs alongside code** | Documentation in repo, not separate wiki |
| **In-process agents** | Function calls, not microservices; zero inter-agent latency |

---

## 4. Onboarding Reading Order

1. `README.md` — what this project does
2. `docs/architecture.md` — how it's built
3. `docs/agent-design.md` — agent responsibilities
4. `docs/data-model.md` — data schemas
5. `docs/workflow-use-cases.md` — test scenarios
6. `docs/voice-extension.md` — voice design
7. `backend/api_server.py` — entry point
8. `backend/orchestrator.py` — agent coordination

---

End of Repository Structure Document
