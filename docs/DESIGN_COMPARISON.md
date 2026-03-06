# Design Comparison: Original (Fergie) vs. Proposed (Syed)

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview | **Date:** March 1, 2026

This document provides a transparent comparison between Fergie Feng's initial design
(commit `8d414f7`, Feb 28 2026) and the revised architecture implemented on the
`PetCare_Syed` branch. It explains **what changed**, **why each change was made**,
and **what was preserved** from the original vision.

---

## 1. Executive Summary

Fergie's original design laid strong conceptual foundations: safety-first philosophy,
layered architecture, modular agents, and separation of concerns. These principles
were fully retained. The changes made on `PetCare_Syed` were **implementation-level
decisions** — choosing specific technologies, restructuring agent topology for safety,
and building a working POC.

**Nothing from Fergie's design was discarded.** It was refined, implemented, and
in several cases strengthened — particularly around safety ordering.

---

## 2. Side-by-Side Comparison

| Dimension | Fergie's Original Design | Syed's Proposed Implementation | Verdict |
|-----------|--------------------------|-------------------------------|---------|
| **Content Scope** | Documentation only (8 files, 0 code) | Full implementation + 30+ docs | Syed extends |
| **Agent Count** | 8 agents | 7 agents | Changed (see §3) |
| **Agent Ordering** | Intake → Triage → Category → Routing → Booking → Safety → Summary | Intake → **Safety Gate** → Confidence Gate → Triage → Routing → Scheduling → Guidance | Changed (see §3) |
| **Framework** | Google ADK (`src/orchestrator/`, `src/specialists/`, `src/tools/`) | Custom Python orchestrator (`backend/orchestrator.py`) | Changed (see §4) |
| **Backend** | FastAPI (suggested) | Flask (implemented) | Changed (see §5) |
| **Database** | PostgreSQL / Firebase (4 relational tables with PKs/FKs) | JSON files (3 config files) | Changed (see §6) |
| **Voice** | "Optional module" — vague provider suggestions | 3-tier architecture with costs, latency, safety, and code | Syed extends |
| **Multilingual** | Not mentioned | 7 languages + RTL support | Syed adds |
| **Deployment** | Not addressed | Docker + docker-compose + Render/Railway + one-click scripts | Syed adds |
| **Workflow Automation** | Not addressed | n8n (actions layer) | Syed adds |
| **Architecture Diagrams** | None (text descriptions only) | 4 Mermaid diagrams (system, pipeline, voice, deployment) | Syed adds |
| **Test Scenarios** | 2 basic workflow use cases | 6 detailed test scenarios with per-agent expected behavior | Syed extends |
| **Data Access Policy** | Mentioned conceptually (5 lines) | Full matrix (7 agents × 5 data stores) | Syed extends |
| **Dev Phases** | 3 phases (vague, no owners/dates) | 6 phases with sprint tasks, owners, and risk register | Syed extends |
| **Safety Philosophy** | ✅ Preserved | ✅ Preserved and strengthened | Aligned |
| **Modular Design** | ✅ Preserved | ✅ Preserved | Aligned |
| **Separation of Concerns** | ✅ Preserved | ✅ Preserved | Aligned |
| **"Not a chatbot" Positioning** | ✅ Preserved | ✅ Preserved | Aligned |

---

## 3. Agent Topology: 8 Agents → 7 Agents

This is the most significant design change. It was made for **safety, simplicity, and correctness**.

### 3.1 Fergie's Original 8-Agent Design

```
Orchestrator → Intake → Triage → Category → Routing → Booking → Safety → Summary
```

| # | Agent | Type |
|---|-------|------|
| — | Orchestrator | Control |
| 1 | Intake Agent | LLM |
| 2 | Triage Agent | LLM |
| 3 | Category Agent | Rules |
| 4 | Routing Agent | Rules |
| 5 | Booking Agent | Rules |
| 6 | Safety Agent | Rules + LLM |
| 7 | Summary Agent | LLM |

### 3.2 Syed's Proposed 7-Agent Design

```
Orchestrator → Intake(A) → Safety Gate(B) → Confidence Gate(C) → Triage(D) → Routing(E) → Scheduling(F) → Guidance(G)
```

| # | Agent | Type |
|---|-------|------|
| — | Orchestrator | Control |
| A | Intake Agent | LLM |
| B | Safety Gate Agent | Rules |
| C | Confidence Gate Agent | Rules |
| D | Triage Agent | LLM |
| E | Routing Agent | Rules |
| F | Scheduling Agent | Rules |
| G | Guidance & Summary Agent | LLM |

### 3.3 What Changed and Why

#### Change 1: Safety Agent moved BEFORE Triage (Critical)

| | Fergie | Syed |
|---|--------|------|
| **Position** | Agent #6 (after Booking) | Agent B (immediately after Intake) |

**Problem with original ordering:** In Fergie's design, the Safety Agent runs *after* Booking.
This means an emergency case (e.g., "my dog ate rat poison and is seizing") would flow through
Triage → Category → Routing → Booking *before* red flags are detected. The system could
book a routine appointment for an emergency before safety guidance fires.

**Proposed fix:** Safety Gate (B) runs immediately after Intake — before any AI reasoning or
scheduling occurs. If a red flag is detected, the pipeline short-circuits to emergency
escalation. No triage, no booking, no delay.

> **Principle:** Red-flag detection must be the FIRST check, not the last.

#### Change 2: Category Agent removed → folded into Routing Agent

**Reasoning:**
- The Category Agent classifies symptoms into a domain (GI, respiratory, skin, etc.).
- The Routing Agent maps that domain to a service line.
- These are tightly coupled — category classification is an intermediate step that only
  exists to feed routing. Having a separate agent adds an extra hop without adding
  independent value.
- In the revised design, the Routing Agent (E) performs both classification and service-line
  mapping in a single rule-based step.

> **Principle:** Merge agents when one agent's only consumer is the next agent in sequence.

#### Change 3: Confidence Gate Agent (C) added

**Reasoning:**
- Fergie's design has no explicit validation step between intake and triage.
- If the Intake Agent misses a critical field (e.g., species, duration), the Triage Agent
  receives incomplete data and produces unreliable urgency scores.
- The Confidence Gate (C) is a deterministic rules-based agent that checks whether all
  required fields are present and scores data completeness. If confidence is low, it
  loops back to the Intake Agent for clarification (max 2 rounds) or flags for
  receptionist review.

> **Principle:** Never let incomplete data reach the Triage Agent — garbage in, garbage out.

#### Change 4: Safety Agent split → Safety Gate (B) + Guidance (G)

**Reasoning:**
- Fergie's Safety Agent had two responsibilities: (1) detect red flags, and
  (2) generate owner guidance.
- These are fundamentally different operations:
  - Red-flag detection is **deterministic** (keyword matching) and must run early.
  - Owner guidance is **generative** (LLM) and requires triage + routing context.
- Splitting them ensures red-flag detection runs at zero cost (rules), while owner
  guidance benefits from the full pipeline context.

> **Principle:** Separate detection (fast, deterministic) from generation (slow, contextual).

#### Change 5: Summary Agent merged into Guidance & Summary Agent (G)

**Reasoning:**
- Owner guidance and the clinic-facing summary share the same context: all upstream
  agent outputs. Running two separate LLM calls with the same input is redundant.
- Merging them into a single agent (G) reduces latency and cost while producing
  both outputs in one pass.

> **Principle:** Merge agents when they share identical inputs and context.

#### Change 6: Booking Agent renamed to Scheduling Agent

**Reasoning:**
- "Booking" implies a completed transaction with confirmation, payment, calendar integration.
- For the POC, the agent only proposes available slots or generates a booking payload — it
  does not complete a real booking.
- "Scheduling" more accurately describes what the agent does in the MVP scope.

> **Principle:** Name agents for what they actually do, not what they aspire to do.

### 3.4 Net Result

| Metric | 8-Agent (Fergie) | 7-Agent (Syed) |
|--------|-----------------|-----------------|
| Total agents | 8 | 7 |
| LLM calls per session | 4 (Intake, Triage, Safety, Summary) | 3 (Intake, Triage, Guidance) |
| Cost per session | ~$0.013 | ~$0.010 |
| Safety gate position | After booking (#6) | After intake (#2) |
| Data validation gate | None | Confidence Gate (#3) |
| Redundant classification step | Category Agent | Folded into Routing |

---

## 4. Framework: Google ADK → Custom Orchestrator

### Fergie's Original

Fergie's `repo-structure.md` specified a **Google ADK** based architecture:

```
src/
├── orchestrator/
│   ├── agent.py              # ADK orchestrator
│   ├── agent_discovery.py    # Auto-register specialists
│   ├── routing_filter.py     # Safety gating
│   └── prompt.py
├── specialists/              # ADK specialist agents
│   ├── intake/
│   ├── triage/
│   ├── category/
│   └── ...
└── tools/                    # ADK tool wrappers
    ├── clinic_rules_tool.py
    ├── schedule_tool.py
    └── ...
```

### Proposed Change

```
backend/
├── orchestrator.py           # Custom Python orchestrator
├── agents/                   # Plain Python agent modules
│   ├── intake_agent.py
│   ├── safety_gate_agent.py
│   └── ...
└── data/                     # JSON config files
```

### Reasoning

| Factor | Google ADK | Custom Orchestrator |
|--------|-----------|---------------------|
| **Setup complexity** | High (ADK install, Google Cloud auth, project config) | Low (pip install, run) |
| **Debugging** | Framework internals obscure control flow | Full visibility — it is plain Python |
| **Assignment fit** | Over-engineered for a POC demo | Right-sized |
| **Learning curve** | Team must learn ADK-specific patterns | Team already knows Python |
| **Lock-in** | Tied to Google Cloud ecosystem | Framework-agnostic |
| **Maturity** | ADK is relatively new (2024); API still evolving | Standard Python — stable |

> **Decision:** Use a custom orchestrator for the POC. Document LangGraph as an optional
> future formalization path (see `PROJECT_PLAN.md` Phase 6). Google ADK is not recommended
> due to lock-in and setup overhead.

---

## 5. Backend: FastAPI → Flask

### Reasoning

| Factor | FastAPI | Flask |
|--------|---------|-------|
| **Async needed?** | No — agents are sequential, not concurrent | No |
| **Static file serving** | Requires `StaticFiles` mount | Built-in (`send_from_directory`) |
| **OpenAPI docs** | Auto-generated (nice, but not needed for POC) | Not needed |
| **Complexity** | Pydantic models, async/await, type annotations | Minimal boilerplate |
| **POC demo** | Over-featured | Right-sized |

Flask serves the frontend directly, handles REST endpoints, and runs the orchestrator — all
in ~200 lines. FastAPI's async/Pydantic features add complexity without POC benefit.

---

## 6. Database: PostgreSQL → JSON Files

### Fergie's Original

Fergie designed a 4-table relational schema:

- `clinic_rules` — 14 fields (rule_id, rule_type, species, condition_key, severity, urgency_level, template_text, version, is_active, effective_from, effective_to, ...)
- `availability_slots` — 10 fields (slot_id, provider_id, service_line, start_ts, end_ts, duration_minutes, status, hold_token, hold_expires_at, ...)
- `appointments` — 10 fields (appointment_id, slot_id FK, service_line, urgency_level, pet_name, species, owner_contact, status, ...)
- `intake_records` — 14 fields (intake_id, appointment_id FK, symptoms_json, urgency_level, red_flags_json, vet_summary_text, ...)

### Proposed Change

3 JSON files:

- `clinic_rules.json` — triage rules, routing maps, provider specialties
- `red_flags.json` — 50+ emergency trigger phrases
- `available_slots.json` — mock appointment schedule

### Reasoning

| Factor | PostgreSQL (4 tables, 48 fields) | JSON (3 files) |
|--------|----------------------------------|-----------------|
| **Setup** | Install Postgres, create DB, run migrations, configure connection | Zero setup — files in repo |
| **Inspection** | SQL queries or pgAdmin | Open file in any editor |
| **POC data volume** | <100 records | <100 records |
| **Schema changes** | Migration scripts | Edit JSON |
| **Deployment** | Separate service / managed DB | Bundled in Docker image |
| **Suitable for production?** | Yes | No |
| **Suitable for POC demo?** | Over-engineered | Right-sized |

> **Note:** Fergie's relational schema is well-designed and would be the correct choice for a
> production deployment. The JSON approach is specifically a POC simplification. The schema
> design is preserved in `docs/architecture/data_model.md` as a production reference.

---

## 7. Voice: Vague Suggestion → 3-Tier Architecture

### Fergie's Original

- Listed possible STT/TTS providers (Google STT, Whisper, Web Speech API, Azure TTS, ElevenLabs)
- Described voice as "optional module" with "Mode A" (voice input) and "Mode B" (full voice)
- Included safety requirements (confirmation, red-flag double check, confidence fallback)
- No implementation, no cost estimates, no latency targets

### Proposed Extension

| Tier | Technology | Cost | Latency | Status |
|------|-----------|------|---------|--------|
| Tier 1 | Browser Web Speech API | Free | ~100ms | Implemented |
| Tier 2 | OpenAI Whisper + TTS | ~$0.02/session | ~1-2s | Implemented |
| Tier 3 | OpenAI Realtime API | ~$0.50/session | <500ms | Documented (stretch) |

**What was preserved from Fergie's design:**
- Safety-first voice philosophy (confirmed)
- Critical field confirmation requirement (confirmed)
- Red-flag double confirmation (confirmed)
- Confidence-based fallback to text (confirmed)
- Voice as I/O wrapper, not decision engine (confirmed)

**What was added:**
- Concrete tier structure with cost/latency tradeoffs
- Implementation code (frontend `app.js` + backend endpoints)
- Multilingual voice configuration (7 languages)
- Noise-handling and failure scenario table

---

## 8. Additional Capabilities (Not in Original)

These features were added on `PetCare_Syed` without any corresponding design in the original:

| Feature | Why It Was Added |
|---------|-----------------|
| **Multilingual support (7 languages)** | Broadens accessibility; demonstrates LLM language capability; RTL support shows engineering depth |
| **n8n workflow automation** | Provides "actions layer" — email alerts, Slack notifications, analytics logging — making the POC feel production-real |
| **Docker + docker-compose** | One-command deployment; reproducible builds; eliminates "works on my machine" issues |
| **Mermaid architecture diagrams** | Visual system documentation that renders directly on GitHub |
| **One-click start scripts** | `start.sh` / `start.ps1` — anyone can run the POC without reading setup docs |
| **Deployment guides** | Step-by-step for Local Python, Docker, Render, Railway |
| **6 detailed test scenarios** | Concrete end-to-end test cases with per-agent expected behavior and validation checklist |
| **Cost estimates** | ~$0.01/session breakdown helps justify the approach to stakeholders |

---

## 9. What Was Fully Preserved from Fergie's Vision

The following elements from Fergie's original design were carried forward **unchanged**
in principle:

1. **Safety-first philosophy** — "No medical diagnosis generation," conservative defaults,
   red-flag escalation
2. **Layered architecture** — Modality Layer → Agent Logic Layer → Data Layer
3. **Agent modularity** — each agent has a single responsibility with clear I/O contracts
4. **Separation of triage and booking** — urgency classification isolated from scheduling
5. **"Not a chatbot" positioning** — "safety-constrained, rule-grounded, modular multi-agent
   orchestration framework"
6. **Role-based data access** — agents only access what they need
7. **Minimal PII storage** — session-only memory, no persistent owner data
8. **Extensibility roadmap** — insurance pre-auth, follow-up care, vaccination reminders,
   telemedicine, analytics dashboard
9. **Voice as optional I/O wrapper** — voice does not alter business logic

---

## 10. Summary of Design Decisions

| Decision | Fergie's Original | Syed's Proposal | Rationale |
|----------|-------------------|-----------------|-----------|
| Safety gate position | After booking (#6) | After intake (#2) | Catch emergencies before any downstream processing |
| Category Agent | Separate agent (#3) | Folded into Routing (E) | Eliminates redundant hop; category only feeds routing |
| Confidence Gate | Not present | Added as agent C | Prevents incomplete data from reaching Triage |
| Safety + Guidance split | Combined Safety Agent | Safety Gate (B) + Guidance (G) | Separates detection (fast, rules) from generation (slow, LLM) |
| Summary Agent | Standalone (#7) | Merged into Guidance (G) | Same context; one LLM call instead of two |
| Framework | Google ADK | Custom Python | Simpler, debuggable, no vendor lock-in, right-sized for POC |
| Backend | FastAPI | Flask | Simpler, serves frontend directly, no async needed |
| Database | PostgreSQL (4 tables) | JSON files (3 files) | Zero setup, sufficient for POC demo data volume |
| Voice | Vague optional module | 3-tier concrete architecture | Actionable design with costs, latency, and implementation |
| Languages | English only | 7 languages + RTL | Accessibility and technical depth |
| Deployment | Not addressed | Docker + cloud guides | Reproducible, one-command demo |
| Automation | Not addressed | n8n actions layer | Post-intake workflows feel production-real |

---

## 11. POC Implementation Status (March 6, 2026)

All design decisions documented above have been implemented and validated in the working POC:

- **All 7 agents** implemented, tested, and passing (Agents A, D, G use GPT-4o-mini; B, C, E, F are rule-based)
- **100% M2 triage tier agreement** across all 6 test scenarios
- **100% M4 red-flag detection rate** across emergency scenarios (zero missed red flags)
- **~11.4s average processing time** per session (well within the <15s target)
- **All consumer features built and working:** multilingual support, voice input (Tier 1), emergency short-circuit path, clarification loops, clinic-ready JSON summaries
- **Safety-first ordering confirmed:** Safety Gate (B) runs immediately after Intake — emergency cases never reach Triage or Scheduling

---

## 12. Conclusion

Fergie's original design document provided the **conceptual foundation**: safety-first
philosophy, multi-agent separation, layered architecture, and clinical responsibility
boundaries. These principles are fully preserved in the implementation.

The changes on `PetCare_Syed` are **implementation refinements** — not philosophical
departures. The most critical change (moving Safety Gate before Triage) directly
strengthens the safety-first principle that Fergie established. The other changes
(framework, backend, database) are right-sizing decisions appropriate for a POC scope.

Fergie's original documentation is preserved in `docs/original_main/` for reference.

---

End of Design Comparison Document
