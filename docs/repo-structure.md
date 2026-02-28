

# 📁 Repository Structure Design

## 1. Purpose

This document defines the repository organization for the PetCare Agentic System.

The structure is designed to support:

- Google ADK-based multi-agent orchestration
- Modular specialist agents
- Static fake clinic data for MVP
- Clear separation between architecture, logic, and data
- Future extensibility without structural refactoring

---

## 2. High-Level Directory Overview

```
petcare-agentic-system/
├── README.md
├── .env
├── .env.example
├── .gitignore
├── LICENSE
│
├── docs/
│   ├── architecture.md
│   ├── agent-design.md
│   ├── data-model.md
│   ├── voice-extension.md
│   ├── safety-policy.md
│   └── repo-structure.md
│
├── data/
│   ├── clinic_rules.json
│   ├── providers.json
│   ├── availability_slots.json
│   └── sample_cases/
│
├── logs/
│
├── src/
│   ├── app.py
│   │
│   ├── orchestrator/
│   │   ├── agent.py
│   │   ├── agent_discovery.py
│   │   ├── routing_filter.py
│   │   └── prompt.py
│   │
│   ├── specialists/
│   │   ├── intake/
│   │   │   ├── agent.py
│   │   │   ├── prompt.py
│   │   │   └── schema.json
│   │   ├── triage/
│   │   ├── category/
│   │   ├── routing/
│   │   ├── booking/
│   │   ├── safety/
│   │   └── summary/
│   │
│   ├── tools/
│   │   ├── clinic_rules_tool.py
│   │   ├── schedule_tool.py
│   │   ├── intake_store_tool.py
│   │   └── file_store.py
│   │
│   └── config/
│       └── settings.py
│
└── templates/
```

---

## 3. Directory Responsibilities

### Root Level

- `README.md` — Project overview and setup instructions
- `.env` / `.env.example` — Environment configuration
- `LICENSE` — License information

---

### docs/

Contains all architectural and design documentation.

- `architecture.md` — High-level system blueprint
- `agent-design.md` — Sub-agent responsibility specification
- `data-model.md` — Database schema and storage model
- `voice-extension.md` — Optional voice module design
- `repo-structure.md` — Repository organization rationale

This keeps documentation separated from implementation.

---

### data/

Contains static fake clinic data for MVP demonstration.

- `clinic_rules.json` — Triage logic, routing mappings, safety templates
- `providers.json` — Doctor and service metadata
- `availability_slots.json` — Simulated scheduling slots
- `sample_cases/` — Example structured inputs for testing/demo

No scripts are used. Data is manually maintained for simplicity.

---

### logs/

Stores runtime logs or demo outputs.

Kept separate to avoid polluting source logic.

---

### src/

Core Google ADK application logic.

#### app.py
Main ADK entrypoint.
Initializes orchestrator and registers agents.

---

### src/orchestrator/

Contains root agent coordination logic.

- `agent.py` — Orchestrator definition
- `agent_discovery.py` — Auto-register specialist agents
- `routing_filter.py` — Safety gating and flow control
- `prompt.py` — Orchestrator system prompt

---

### src/specialists/

Each sub-agent is isolated in its own folder.

Each agent folder contains:

- `agent.py` — Agent logic
- `prompt.py` — Agent-specific system prompt
- `schema.json` — Structured output schema

This ensures modularity and responsibility isolation.

---

### src/tools/

ADK tool wrappers.

- `clinic_rules_tool.py` — Reads rule configuration from data/
- `schedule_tool.py` — Reads/writes availability slots
- `intake_store_tool.py` — Persists intake records
- `file_store.py` — Shared JSON read/write helper

Tools abstract data access so agents remain logic-focused.

---

### src/config/

Configuration layer.

- `settings.py` — Environment variables, feature flags (e.g., voice enabled/disabled)

---

### templates/

Optional reusable templates (e.g., vet summary format).

---

## 4. Design Rationale

This repository structure follows these principles:

- Separation of concerns (logic, data, documentation)
- Agent modularity (each specialist self-contained)
- Tool abstraction (data access isolated)
- Voice treated as optional extension
- No UI dependency (ADK-first workflow)

The structure allows future transition from static JSON to a production database without restructuring the agent layer.

---

End of Repository Structure Document