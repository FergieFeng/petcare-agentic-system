# System Overview

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview | **Date:** March 1, 2026

---

## Purpose

The PetCare Triage & Smart Booking Agent automates veterinary clinic intake by collecting pet symptoms, detecting emergencies, classifying urgency, routing to the correct appointment type, and producing structured handoff summaries for the clinical team -- all while providing safe, non-diagnostic guidance to pet owners.

## High-Level Architecture

1. **Input Layer**
   - Accepts owner free-text describing pet symptoms, species, and basic profile via web chat interface.

2. **Content-Safety Guardrails (Pre-Intake) — Two-Stage Pipeline**
   - **Stage 1 — Regex fast-path** (`backend/guardrails.py`): runs before any LLM call, ~0ms, zero API cost.
     - 8 categories: prompt injection / jailbreak (OWASP LLM01, LLM07), data extraction (OWASP LLM02), violence / weapons, sexual / explicit, human-as-pet, substance abuse, abuse / harassment, trolling / off-topic.
     - Leet-speak normalization, multilingual patterns (FR, ES, ZH, AR, HI, UR), pet-medical context exemptions.
     - Also handles: deceased pet (compassionate close), non-pet subjects (redirect), normal animal behavior.
     - 181-case test suite.
   - **Stage 2 — LLM semantic classifier** (GPT-4o-mini, opt-in via `GUARDRAIL_LLM_ENABLED`): screens messages that pass Stage 1 for semantic attacks — paraphrased jailbreaks, indirect prompt injection, and context-manipulation that regex cannot detect. Adds ~300-500ms per turn. **Enabled by default in production** (`GUARDRAIL_LLM_ENABLED=true`).
   - **Audit trail**: every Stage 2 classifier call is traced in LangSmith as `guardrail.llm_classifier` (tag `llm_classifier`) — filterable in the dashboard for real-time safety audit.
   - **Fail-open design**: if the classifier API call fails, the message passes through — legitimate users are never blocked by a classifier outage.

3. **Intake Layer (Sub-Agent A)**
   - Conducts adaptive, multi-turn symptom collection with species-specific follow-up questions.

3. **Safety Layer (Sub-Agent B)**
   - Rule-based red-flag detection; immediately escalates emergencies.

4. **Validation Layer (Sub-Agent C)**
   - Confidence gate: verifies required fields are captured and signals are coherent.

5. **Analysis Layer (Sub-Agents D + E)**
   - Triage Agent: classifies urgency tier (Emergency / Same-day / Soon / Routine).
   - Routing Agent: maps symptom category to appointment type and provider pool.

6. **Action Layer (Sub-Agent F)**
   - Scheduling Agent: proposes available slots or generates booking request.

7. **Output Layer (Sub-Agent G)**
   - Produces owner-facing guidance ("do/don't while waiting") and clinic-facing structured JSON summary.

8. **Orchestration Layer**
   - Coordinates execution order, manages session state, resolves conflicts, enforces safety rules.

## Architecture Diagram

![PetCare Triage Workflow](../images/architecture_workflow.png)

## Detailed Workflow (Step 2 -- Sub-Agent Design)

The architecture diagram above illustrates the full branching workflow:

### Happy Path (No Red Flags, High Confidence)

```
Trigger (owner starts intake)
  → Content-Safety Guardrails (8-category pre-intake screen — blocks abuse, injection, violence, etc.)
  → Sub-Agent A: Intake (collect pet profile + chief complaint + timeline + key symptoms)
  → Sub-Agent A (cont.): Ask adaptive follow-ups by symptom area (GI / resp / skin / injury / behavior)
  → Sub-Agent B: Safety Gate (red-flag symptoms present?)
       → No red flags
  → Sub-Agent C: Confidence Gate (required fields complete AND confidence high enough?)
       → Yes, confidence OK
  → Sub-Agent D: Triage (assign urgency tier: Emergency / Same-day / Soon / Routine)
  → Sub-Agent E: Routing (category → appointment type / provider pool)
  → Sub-Agent F: Scheduling (propose slots OR create booking request)
  → Sub-Agent G: Guidance + Summary (owner do/don't + clinic-facing structured summary)
```

### Emergency Path (Red Flags Detected)

```
Sub-Agent B: Safety Gate → Red-flag symptoms detected
  → Emergency Escalation (B): Advise urgent care now + notify clinic, stop booking flow
  → Document & close
  → Sub-Agent G: Guidance + Summary (emergency-specific guidance + clinic alert)
```

### Clarification Loop (Low Confidence)

```
Sub-Agent C: Confidence Gate → Required fields missing OR confidence too low
  → Clarify / Human Review (C): Ask targeted questions OR mark "needs receptionist review"
  → Loop back to Sub-Agent A: Intake (gather missing info)
  → Re-enter flow at Sub-Agent B: Safety Gate
  (max 2 clarification loops before routing to human)
```

## Technology Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Backend Server** | Python 3.10+ / Flask + Gunicorn | Serves API + static frontend; Gunicorn production server (2 workers, 120s timeout) |
| **Auth Middleware** | HTTP Basic Auth (Flask) | Credentials from env vars only (`AUTH_ENABLED`, `AUTH_USERNAME`, `AUTH_PASSWORD`) — never hardcoded |
| **Session Store** | Two-tier in-memory dict | Active sessions (1hr TTL) + completed sessions (24hr TTL for PDF download); background cleanup every 10 min |
| **LLM Provider** | OpenAI GPT-4o-mini | Configurable via `.env`; Claude fallback planned post-POC |
| **Agent Framework** | Custom Python Orchestrator | POC: no LangGraph/ADK; keeps flow simple and debuggable. Post-POC: LangGraph optional for formal graph; Google ADK not recommended. |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript | Inter font, warm teal theme (`#0d9488`), dark mode, RTL for AR/UR; PWA (manifest.json + service worker) |
| **Data Contracts** | JSON schemas | Structured I/O between all agents |
| **Containerization** | Docker | Single-container deployment |
| **Deployment** | **Render** (Gunicorn + Docker) | Auto-deploy from GitHub, HTTPS, minimal config |
| **Tracing** | LangSmith | Opt-in via `LANGCHAIN_TRACING_V2=true`; traces all 3 LLM agents + guardrail classifier under named spans; filterable by tag (`llm_classifier`, `orchestrator`) |

## Data Sources

**Operational (used at runtime):**

| Source | What It Provides | Agent(s) Using It |
|--------|-----------------|------------------|
| `backend/data/clinic_rules.json` | Clinic routing maps, provider list, species notes | Routing (E) |
| `backend/data/red_flags.json` | 50+ curated emergency triggers | Safety Gate (B) |
| `backend/data/available_slots.json` | Mock clinic schedule | Scheduling (F) |

**Design references (not used at runtime):** HuggingFace pet-health-symptoms-dataset, Vet-AI Symptom Checker, SAVSNET/PetBERT, ASPCA — consulted for domain context and for curating the operational files above. Not loaded or called by the system.

**Deployment:** Render (Docker + Gunicorn). Webhook/n8n optional (`N8N_WEBHOOK_URL` env var).

## Voice Interaction Layer

The system supports three tiers of voice interaction, enabling hands-free intake (ideal for pet owners holding a distressed pet):

| Tier | Technology | Cost | Latency | Best For |
|------|-----------|------|---------|----------|
| **Tier 1** | Browser Web Speech API | Free | ~100ms | Quick POC demo, Chrome/Edge users |
| **Tier 2** | OpenAI Whisper (STT) + `tts-1-hd` TTS | ~$0.02/session | ~1-2s | Consistent quality across all browsers; HD model with natural pacing (`speed=0.95`) |
| **Tier 3** | OpenAI Realtime API (WebSocket) | ~$0.50-1.00/session | <500ms | Natural voice conversation (stretch goal) |

**Architecture:**
- Tiers 1 & 2 are fully implemented: "voice-to-text + text-to-voice" wrappers around the existing text pipeline — no changes to the agent pipeline
- Tier 2 TTS uses the `tts-1-hd` model (significantly less robotic than `tts-1`) at `speed=0.95` for natural, unhurried pacing — implemented for all 7 languages
- Tier 3 (Realtime API) is a stretch goal
- Voice endpoints: `/api/voice/transcribe` (Whisper STT) and `/api/voice/synthesize` (OpenAI TTS `tts-1-hd`)

See [TECH_STACK.md](../../TECH_STACK.md) for full voice tier comparison and implementation details. **MVP:** Baseline evaluation and demo are **text-based**; voice is optional and does not affect the four evaluation metrics.

## Evaluation and baseline comparison

The system is evaluated against a **manual receptionist phone-script baseline** (Option 1 in [BASELINE_METHODOLOGY.md](../BASELINE_METHODOLOGY.md)). The same test scenarios are run through both baseline and agent; the same four metrics are measured:

| Metric | Where it is measured / produced |
|--------|---------------------------------|
| **Time to complete intake** | Session timestamps: `created_at`, first user message time, and state transition to `complete` or `emergency`; pipeline `metadata.processing_time_ms` per request. Evaluator computes wall-clock from first message to intake complete. |
| **Required fields captured** | Confidence Gate (C) output: `missing_required` and `required_fields_captured_pct` (M1). Exposed in `agent_outputs.confidence_gate` and in session summary for scoring. |
| **Triage accuracy** | Triage Agent (D) output: `urgency_tier` in `agent_outputs.triage`. Compared to gold labels per scenario. |
| **Red-flag detection** | Safety Gate (B) output: `red_flag_detected` and `red_flags` in `agent_outputs.safety_gate`. Target 100% on red-flag scenarios. |

Session summary (`GET /api/session/<id>/summary`) and response metadata provide the data needed to fill the baseline-vs-agent results table (M1–M6) for the report and demo.

## Design Characteristics

- **Safety-first:** red-flag detection runs before any routing or scheduling.
- **Two-stage guardrails:** regex fast-path (Stage 1, 0ms) + LLM semantic classifier (Stage 2, ~300-500ms) — production default on.
- **Composable:** each sub-agent can be swapped or improved independently.
- **Auditable:** every triage decision maps to symptom evidence; every guardrail classifier call is traced in LangSmith.
- **Schema-driven:** outputs follow strict validation for clinic integration.
- **Provider-agnostic:** orchestration can call different LLM providers.
- **Text-first MVP:** core pipeline and baseline evaluation are text-based; voice Tier 1 + Tier 2 implemented (`tts-1-hd`, free-flowing intake); Tier 3 stretch.
- **Secure by default:** HTTP Basic Auth middleware (env-var credentials only); two-tier session TTLs; background cleanup timer; Flask-Limiter rate limiting; plausibility validation in intake agent.

## Architectural Positioning

This system is not merely a chatbot. It is a **safety-constrained, rule-grounded, modular multi-agent orchestration framework** designed for operational veterinary environments.

The primary innovation lies in **structured triage enforcement and routing intelligence** — not conversational novelty. Every design choice prioritizes clinical safety, explainability, and operational reliability over conversational fluency or feature breadth.

Key differentiators from a generic chatbot:

- **Deterministic safety layer** runs before any AI reasoning — red flags trigger escalation regardless of LLM output
- **Mixed execution** — safety-critical agents are rule-based (zero cost, deterministic); only reasoning-heavy agents call the LLM
- **Structured outputs** — every response follows a validated schema; clinic summaries are machine-readable JSON
- **Explicit autonomy boundaries** — the agent never diagnoses, prescribes, or overrides clinic rules
- **Auditable decision chain** — every triage decision traces through the full agent pipeline with evidence

## Enhanced Features (v1.1-poc)

In addition to the core 7-agent pipeline (100% M2 triage accuracy, 100% M4 red-flag detection), the system includes:

| Feature | Technology | Description |
|---------|-----------|-------------|
| **Streaming Responses** | Server-Sent Events (SSE) | Real-time token streaming for natural, progressive chat responses |
| **Nearby Vet Finder** | Google Places API + OpenStreetMap Nominatim fallback | Finds real veterinary clinics near the user with ratings, phone, distance, and directions; falls back to Nominatim when Places API is unavailable |
| **PDF Triage Export** | fpdf2 (server-side) | Downloadable summary with pet info, symptoms, triage result, appointments, and guidance; available via completed session store (24hr TTL) |
| **Photo Analysis** | OpenAI Vision (GPT-4o-mini) | Upload a photo of symptoms for AI visual observation (never diagnoses) |
| **Pet Profile Persistence** | Browser localStorage | Remembers species, name, breed, age across sessions for returning users |
| **Symptom History** | Browser localStorage | Tracks past visits with date, complaint, and urgency for recurring symptom awareness |
| **Cost Estimator** | Orchestrator output | Estimated cost range for the recommended appointment type |
| **Feedback Rating** | Frontend + API | Users can rate the triage experience after completion |
| **Follow-up Reminders** | Browser Notifications API | Opt-in browser notifications for follow-up care reminders |
| **Breed-Specific Risk Alerts** | Intake Agent enrichment | Flags known breed-specific health risks during intake |
| **Dark Mode** | CSS custom properties | System-preference-aware dark theme toggle |
| **PWA Support** | manifest.json + service worker (sw.js) | Installable as a Progressive Web App with offline shell |
| **Chat Transcript Export** | Frontend JS | Export full conversation as text file |
| **Animated Onboarding** | CSS/JS animations | First-time user guided walkthrough |
| **Consent Banner** | Frontend component | Cookie/data consent banner for privacy compliance |
| **Appointment Booking** | Orchestrator post-completion flow | Users can confirm an appointment by name or position after triage |

### Multilingual Support

The system supports **7 languages** with full UI translation:

| Code | Language | Notes |
|------|----------|-------|
| `en` | English | Default |
| `fr` | French | |
| `zh` | Chinese (Simplified) | |
| `ar` | Arabic | RTL layout |
| `es` | Spanish | |
| `hi` | Hindi | |
| `ur` | Urdu | RTL layout |

## Non-Goals (POC Phase)

- Providing medical diagnoses or prescriptions
- Integrating with real EMR/CRM systems
- Multi-clinic deployment
- Payment processing

## Success Criteria

- Triage tier agreement with clinic staff ≥ 80%
- Routing accuracy ≥ 80%
- Intake completeness ≥ 90%
- Full intake flow completes in < 15 seconds (excluding interactive turns)
- Zero missed emergency red flags in test set
