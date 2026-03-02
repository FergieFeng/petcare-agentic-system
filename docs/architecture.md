# PetCare Agentic System Architecture

**Author:** Syed Ali Turab | **Date:** March 1, 2026

---

## 1. System Vision

PetCare Agentic System is a safety-first, multi-agent veterinary triage and smart booking framework designed to reduce clinic call overload while maintaining clinical responsibility boundaries.

The system focuses on structured intake, urgency triage, intelligent routing, and appointment coordination — without generating medical diagnoses.

---

## 2. High-Level Architecture Overview

The system follows a layered architecture model:

### Layer 1 — Modality Layer (Input / Output)

- Text Chat Interface (Primary)
- Voice Interface (3-Tier Enhancement)

Voice is treated strictly as an input/output wrapper and does not alter business logic.

| Tier | Technology | Cost | Latency |
|------|-----------|------|---------|
| **Tier 1** | Browser Web Speech API | Free | ~100ms |
| **Tier 2** | OpenAI Whisper (STT) + TTS | ~$0.02/session | ~1-2s |
| **Tier 3** | OpenAI Realtime API (WebSocket) | ~$0.50/session | <500ms |

```
Voice → Speech-to-Text → Core Logic → Text Output → Text-to-Speech (Optional)
```

The system also supports **7 languages** (English, French, Chinese, Arabic, Spanish, Hindi, Urdu) with RTL layout for Arabic and Urdu.

---

### Layer 2 — Multi-Agent Logic Layer

This layer contains 7 modular agents coordinated by a central orchestrator, using a **custom Python orchestrator** (no framework — simpler and sufficient for POC).

Core responsibilities:

| Agent | Type | Responsibility |
|-------|------|---------------|
| **A — Intake** | LLM | Structured symptom collection with adaptive follow-ups |
| **B — Safety Gate** | Rules | Red-flag detection, emergency escalation |
| **C — Confidence Gate** | Rules | Field validation, confidence scoring, clarification loops |
| **D — Triage** | LLM | Urgency classification (Emergency / Same-day / Soon / Routine) |
| **E — Routing** | Rules | Symptom categorization + appointment type mapping |
| **F — Scheduling** | Rules | Slot matching from clinic schedule |
| **G — Guidance & Summary** | LLM | Owner do/don't guidance + clinic-facing structured JSON |

Each agent has a clearly defined responsibility boundary to reduce coupling and maintain safety constraints. Only 3 agents make LLM API calls (~$0.01/session); the other 4 are deterministic rule-based agents with zero cost.

---

### Layer 3 — Data Layer

The data layer stores operational and configuration data required for system function.

| Data Store | Format | Read By | Write By |
|-----------|--------|---------|----------|
| `clinic_rules.json` | Static JSON | Triage (D), Routing (E) | None (clinic-managed) |
| `red_flags.json` | Static JSON | Safety Gate (B) | None (curated list) |
| `available_slots.json` | Static JSON | Scheduling (F) | Scheduling (F) in production |
| Intake Records | In-memory dict | Guidance (G), Orchestrator | Guidance (G) |
| Appointments | In-memory dict | Orchestrator | Scheduling (F) |

Data access follows role-based boundaries to prevent cross-responsibility leakage. See [data-model.md](data-model.md) for full schema specs.

### Layer 4 — Actions Layer (n8n)

Post-intake automation handled by n8n workflow engine (separate Docker container):

- Emergency Alert → Slack + Email to on-call vet
- Clinic Summary Delivery → Formatted email + Google Sheets log
- Appointment Confirmation → Email to pet owner
- Analytics Logger → Session metrics to Google Sheets

---

## 3. End-to-End Workflow

### Happy Path (No Red Flags, High Confidence)

```
1. Owner submits symptom description
2. Intake Agent (A) structures key fields via adaptive follow-ups
3. Safety Gate (B) checks for emergency red flags → NONE
4. Confidence Gate (C) validates completeness → PASS
5. Triage Agent (D) assigns urgency tier
6. Routing Agent (E) classifies category + selects service line
7. Scheduling Agent (F) proposes available slots
8. Guidance & Summary Agent (G) generates owner guidance + clinic JSON
9. Orchestrator assembles final response
```

### Emergency Path (Red Flags Detected)

```
Safety Gate (B) → Red-flag symptoms detected
  → Emergency Escalation: "Seek emergency care immediately"
  → Skip Confidence, Triage, Routing, Scheduling
  → Guidance Agent (G) generates emergency-specific guidance
  → n8n triggers Emergency Alert workflow
```

### Clarification Loop (Low Confidence)

```
Confidence Gate (C) → Required fields missing or confidence too low
  → Ask targeted clarifying questions
  → Loop back to Intake Agent (A)
  → Max 2 loops before routing to human receptionist
```

---

## 4. Design Principles

### Safety-First
- No diagnosis generation
- Deterministic red-flag detection runs before any AI reasoning
- Red-flag escalation is mandatory — cannot be overridden by LLM
- Conservative defaults: when uncertain, escalate rather than under-triage

### Separation of Concerns
- Triage logic isolated from booking logic
- Safety detection (B) separated from guidance generation (G)
- Routing logic separated from intake logic
- Voice separated from core system logic

### Modularity
- Agents can be extended or replaced independently
- Voice and telephony can be added without altering triage core
- n8n workflows are decoupled from agent logic

### Mixed Execution
- Safety-critical agents (B, C) are deterministic rules — zero cost, zero latency
- Reasoning-heavy agents (A, D, G) call LLM APIs
- This reduces cost and ensures safety decisions are never dependent on LLM availability

---

## 5. Architectural Positioning

This system is not merely a chatbot. It is a **safety-constrained, rule-grounded, modular multi-agent orchestration framework** designed for operational veterinary environments.

The primary innovation lies in **structured triage enforcement and routing intelligence** — not conversational novelty. Key differentiators:

- Deterministic safety layer runs before any AI reasoning
- Mixed execution (rules + LLM) reduces cost and increases reliability
- Structured outputs follow validated schemas for clinic integration
- Explicit autonomy boundaries — the agent never diagnoses or prescribes
- Auditable decision chain — every triage decision traces through the full pipeline

---

## 6. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.11 + Flask | API server, static file serving |
| **Frontend** | Vanilla HTML/CSS/JS | Chat UI, voice controls, multilingual |
| **LLM** | OpenAI GPT-4.1-mini / Anthropic Claude | Agent reasoning |
| **Voice** | Whisper (STT) + OpenAI TTS | Voice I/O |
| **Orchestration** | Custom Python Orchestrator | Agent coordination (no LangGraph/ADK for POC) |
| **Automation** | n8n (Docker container) | Post-intake workflows |
| **Containerization** | Docker + docker-compose | Deployment |
| **Hosting** | Render / Railway | Free-tier cloud |

---

## 7. Development Phases

| Phase | Focus | Timeline |
|-------|-------|----------|
| **Phase 1** | Core text-based triage (7 agents + orchestrator) | Weeks 1-2 |
| **Phase 2** | Voice support (3 tiers) + multilingual (7 languages) | Weeks 3-4 |
| **Phase 3** | Docker + deployment pipeline | Week 5 |
| **Phase 4** | n8n workflow automation | Week 6 |
| **Phase 5** | Evaluation & testing | Week 7 |
| **Phase 6** | Report, video & polish | Week 8 |

---

## 8. Future Extensions

- Insurance pre-authorization agent
- Follow-up care agent
- Vaccination reminder automation
- Telemedicine integration
- Analytics dashboard
- Formal orchestration (LangGraph — optional post-POC)

---

End of Architecture Document
