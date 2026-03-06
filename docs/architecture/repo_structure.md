# Repository Structure

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview | **Date:** March 1, 2026

---

## 1. Purpose

This document defines the repository layout for the PetCare Triage & Smart Booking Agent. The structure supports:

- Flask-based API server with in-process agent orchestration
- Modular sub-agent design (7 agents + orchestrator)
- Static frontend served by Flask
- Docker containerization (single container; deployed on Render)
- Comprehensive documentation separated from implementation

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
├── .env.example                    # Environment variable template (copy to .env)
├── .gitignore                      # Git ignore rules
├── requirements.txt                # Python dependencies (pip install -r)
├── Dockerfile                      # Single-container Docker build
├── docker-compose.yml              # Multi-container (optional; includes n8n for local dev)
├── start.sh                        # One-click Docker start (macOS/Linux)
├── start.ps1                       # One-click Docker start (Windows)
│
├── backend/                        # Python backend (Flask API + agents)
│   ├── __init__.py                 # Package marker
│   ├── api_server.py               # Flask app, REST endpoints, HTTP Basic Auth middleware, static serving
│   ├── orchestrator.py             # Agent orchestration, workflow control, two-tier session store
│   │
│   ├── agents/                     # Sub-agent implementations
│   │   ├── __init__.py
│   │   ├── intake_agent.py         # Agent A: symptom collection, adaptive follow-ups
│   │   ├── safety_gate_agent.py    # Agent B: red-flag detection, emergency escalation
│   │   ├── confidence_gate.py      # Agent C: field validation, confidence scoring
│   │   ├── triage_agent.py         # Agent D: urgency classification (4 tiers)
│   │   ├── routing_agent.py        # Agent E: symptom category → appointment type
│   │   ├── scheduling_agent.py     # Agent F: slot matching, booking request
│   │   └── guidance_summary.py     # Agent G: owner guidance + clinic summary
│   │
│   ├── data/                       # Static data files (POC — replaces a database)
│   │   ├── clinic_rules.json       # Triage rules, routing maps, provider list
│   │   ├── red_flags.json          # 50+ emergency trigger phrases
│   │   └── available_slots.json    # Mock appointment schedule
│   │
│   └── logs/                       # Runtime logs (gitignored except .gitkeep)
│       └── .gitkeep
│
├── frontend/                       # Client-side UI (vanilla HTML5/CSS3/JS, Inter font, teal #0d9488)
│   ├── index.html                  # Chat interface, language selector, voice controls, dark mode toggle
│   ├── manifest.json               # PWA manifest (installable web app)
│   ├── sw.js                       # Service worker for PWA offline shell
│   ├── icons/                      # PWA app icons (multiple sizes)
│   ├── js/
│   │   └── app.js                  # Chat logic, voice, multilingual (7 langs), streaming, API calls
│   └── styles/
│       └── main.css                # Responsive styling, RTL support (AR/UR), dark theme, Inter font
│
├── docs/                           # Documentation
│   ├── architecture/               # System design documents
│   │   ├── README.md               # Architecture docs index
│   │   ├── system_overview.md      # High-level architecture, tech stack, data sources
│   │   ├── agents.md               # Sub-agent specs, I/O contracts, data access policy
│   │   ├── orchestrator.md         # Orchestrator responsibilities, workflow, branching
│   │   ├── data_model.md           # Data schemas, access policy, privacy guidance
│   │   ├── output_schema.md        # Canonical output JSON schema
│   │   ├── repo_structure.md       # This file — repository layout
│   │   ├── scope_and_roles.md      # Project scope, agent roles
│   │   ├── workflow_technical.md   # Technical workflow (with code flow)
│   │   └── workflow_non_technical.md # Non-technical workflow (plain language)
│   │
│   ├── agent_specs/                # Per-agent detailed specifications
│   │   ├── TASK_ASSIGNMENT.md      # Agent development task tracker
│   │   ├── intake/                 # Agent A spec + test fixtures
│   │   ├── safety_gate/            # Agent B spec + test fixtures
│   │   ├── confidence_gate/        # Agent C spec + test fixtures
│   │   ├── triage/                 # Agent D spec + test fixtures
│   │   ├── routing/                # Agent E spec + test fixtures
│   │   ├── scheduling/             # Agent F spec + test fixtures
│   │   ├── guidance_summary/       # Agent G spec + test fixtures
│   │   └── orchestrator/           # Orchestrator spec + test fixtures
│   │
│   ├── images/                     # Architecture diagrams and visuals
│   │   └── architecture_workflow.png
│   │
│   ├── original_main/             # Preserved docs from the main branch
│   │   ├── architecture.md
│   │   ├── agent-design.md
│   │   ├── data-model.md
│   │   ├── voice-extension.md
│   │   ├── workflow-use-cases.md
│   │   ├── repo-structure.md
│   │   └── changelog.md
│   │
│   ├── test_scenarios.md           # End-to-end test cases + validation checklist
│   └── CHANGELOG.md                # Project changelog and reading order
```

---

## 3. Directory Responsibilities

### Root Level

Configuration, deployment, and top-level documentation files. These are the first files a new developer reads.

| File | Purpose |
|------|---------|
| `README.md` | Project overview, mermaid architecture diagrams, quick start |
| `PROJECT_PLAN.md` | 6-phase development roadmap with owners, status, risks |
| `TECH_STACK.md` | Full technology stack with runtime architecture diagrams |
| `DEPLOYMENT_GUIDE.md` | Step-by-step guides for local, Docker, Render, Railway |
| `technical_report.md` | MMAI 891 assignment report template |
| `requirements.txt` | Python package dependencies |
| `Dockerfile` | Single-container Docker image definition |
| `docker-compose.yml` | Multi-container setup (optional; includes n8n for local dev) |

### `backend/`

All server-side Python code. The Flask API server (`api_server.py`) is the single entry point — it serves the frontend as static files, exposes REST endpoints, and applies HTTP Basic Auth middleware (credentials from `AUTH_ENABLED`, `AUTH_USERNAME`, `AUTH_PASSWORD` env vars only). The orchestrator manages a two-tier session store (active 1hr TTL + completed 24hr TTL) with background cleanup. Agents are isolated Python modules with standardized I/O contracts. In production, the app runs under Gunicorn (2 workers, 120s timeout).

### `backend/agents/`

Each file implements one sub-agent with a standardized interface:
- `process(input_data)` → returns structured output dict
- LLM-backed agents (A, D, G) call external APIs
- Rule-based agents (B, C, E, F) run locally with zero API cost

### `backend/data/`

Static JSON files that serve as the POC's data layer. In production, these would be replaced by database tables. See `docs/architecture/data_model.md` for field-level schemas.

### `frontend/`

Vanilla HTML5/CSS3/JS — no build step, no npm, no framework. Served directly by Flask. Uses Inter font with warm teal theme (`#0d9488`). Includes: dark mode, 7-language multilingual support (EN, FR, ZH, AR, ES, HI, UR), RTL layout for AR/UR, 3-tier voice interaction, PWA support (manifest.json + service worker), streaming responses, pet profile persistence (localStorage), symptom history, PDF export, photo analysis upload, Google Places vet finder (with Nominatim fallback), cost estimator, feedback rating, follow-up reminders (browser notifications), breed-specific risk alerts, chat transcript export, animated onboarding, and consent banner.

### `docs/`

All documentation, organized by topic. Architecture docs describe the system design. Agent specs provide per-agent details and test fixtures (intake, safety_gate, triage, routing, scheduling, guidance_summary, orchestrator). The `original_main/` folder preserves the foundational docs from the main branch for reference.

---

## 4. Design Rationale

| Principle | How It's Applied |
|-----------|-----------------|
| **Separation of concerns** | Backend logic, frontend UI, data, and documentation are in separate directories |
| **Agent modularity** | Each agent is a self-contained Python module with its own spec doc |
| **No build step** | Frontend is vanilla HTML/CSS/JS — no webpack, no npm, no transpiling |
| **Data abstraction** | Agents read from JSON files via a consistent interface; swapping to a database changes only the data layer |
| **Voice as a layer** | Voice endpoints live in `api_server.py` but don't alter agent logic |
| **Docker-first** | The entire app runs in a single Docker container; deployed to Render via Dockerfile |
| **Docs alongside code** | Documentation lives in `docs/` next to the source, not in a separate wiki |

---

## 5. Key Files for New Developers

If you're onboarding, read in this order:

1. `README.md` — what this project does
2. `TECH_STACK.md` — how it's built and deployed
3. `docs/architecture/system_overview.md` — architecture and workflow
4. `docs/architecture/agents.md` — sub-agent responsibilities and contracts
5. `docs/architecture/data_model.md` — data schemas and access policy
6. `docs/test_scenarios.md` — concrete test cases
7. `backend/api_server.py` — entry point for the backend
8. `backend/orchestrator.py` — how agents are coordinated
9. `PROJECT_PLAN.md` — what's done and what's next

---

End of Repository Structure Document
