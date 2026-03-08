# Changelog

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview | **Date:** March 1, 2026

---

## Purpose

This file tracks the evolution of the PetCare Triage & Smart Booking Agent project. It serves as a handoff document for collaborators and a quick reference for what has been built, when, and in what order.

---

## Branch: `enhance/guardrail-llm-production-default` → `main` — Guardrail LLM Default + Voice/Intake UX + Full Docs Refresh

### 2026-03-07 — LLM Guardrail Production Default + Voice UX + Documentation Sweep

**Tag:** `poc/guardrail-production-v1.1`

**Guardrail LLM Classifier — Production Default On:**
- `GUARDRAIL_LLM_ENABLED` changed from `false` to `true` in `.env.example`
- `.env.example` comment updated: production recommendation explicitly stated; local dev note to set `false` for faster iteration
- Every message passing Stage 1 regex now screened by GPT-4o-mini for semantic attacks by default
- Cost: ~$0.10/day at typical POC traffic — negligible for production safety gain
- Every Stage 2 decision traced in LangSmith under `guardrail.llm_classifier` with tag `llm_classifier`

**Voice UX Hardening** (`backend/api_server.py`, `backend/agents/intake_agent.py`):
- TTS model upgraded: `tts-1` → `tts-1-hd` — significantly less robotic across all 7 languages
- TTS speed set to `0.95` — natural, unhurried pacing (was default, slightly fast)
- Intake `temperature`: `0.1` → `0.3` — more natural, varied phrasing
- System prompt rewritten from rigid field-collection rules to warm conversational receptionist style
- `intake_complete=True` fires as soon as species + chief_complaint known — no longer blocks on timeline/eating/energy
- All date/duration formats accepted verbatim in `symptom_details.timeline` ("since Monday", "about a week", "started yesterday", "since March 1st")

**Documentation Sweep (all docs updated to reflect current state):**
- `docs/architecture/system_overview.md`: two-stage guardrail section, LangSmith row in tech stack, `tts-1-hd` in voice tier table, updated design characteristics
- `docs/architecture/agents.md`: Pre-Intake Guardrails entry expanded to two-stage pipeline with audit trail; Intake Agent entry updated for free-flowing UX
- `docs/architecture/orchestrator.md`: Safety Enforcement invariants updated for two-stage pipeline
- `TECH_STACK.md`: AI/LLM table (guardrail classifier row, `tts-1-hd`, LangSmith row); cost table; Python dependencies (flask-limiter, langsmith); Security & Privacy table (rate limiting, two-stage guardrails, input validation, output sanitization, TTS policy); Voice Layer (`tts-1-hd`); External API Integrations
- `docs/AGENT_DESIGN_CANVAS.md`: guardrails section expanded to two-stage; added STEP 7 (Voice & Intake UX Hardening); LLM remediations table updated with Stage 2 classifier as 4th entry
- `docs/SECURITY_AUDIT.md`: LLM01 residual risk updated to Low (Stage 2 classifier addresses semantic attack gap)
- `docs/CHANGELOG.md`: this entry

---

## Branch: `main` — Security Hardening + OWASP LLM Audit

### 2026-03-07 — Security: Traditional Pentest + OWASP LLM Top 10 Audit + 3 Remediations

**Traditional Web Vulnerability Pentest** (`backend/security_pentest.py`):
- Black-box OSCP-style pentest against live Render deployment
- 6 vulnerabilities identified across rate limiting, TTS content policy, field scrubbing, error disclosure, and input validation
- All 6 remediated — post-pentest re-run: 9/9 tests passed/blocked
- Full findings documented in `docs/SECURITY_AUDIT.md` (Sections 1–7)

**OWASP LLM Top 10 Assessment** (`backend/llm_pentest.py`):
- 19 black-box tests across 7 LLM vulnerability categories (LLM01–LLM09)
- Results: 15 protected, 3 partial, 1 vulnerable — posture: PARTIAL
- Results artifact saved to `backend/llm_security_report.json`
- Full findings in `docs/SECURITY_AUDIT.md` Section 8

**Three LLM Remediations Applied:**
- **LLM09-9A** (`backend/agents/intake_agent.py`): Added `_check_plausibility()` classmethod + `_SPECIES_IMPOSSIBLE_SYMPTOMS` dict to reject anatomically impossible species/symptom combinations (e.g. fish barking); LLM rule 10 added as soft layer
- **LLM02-2A** (`backend/api_server.py`): Added `_escape_pet_profile()` — HTML-encodes user-supplied fields (`pet_name`, `breed`, `age`, `weight`) at API output boundary in `get_summary()`
- **LLM07-7B** (`backend/api_server.py`): Added `_TTS_BLOCKED_PATTERNS` (8 compiled regex patterns) and `_tts_policy_check()` — blocks dosage language, prescription verbs, vet identity claims, named diagnoses, named antidotes from TTS synthesis

**Rate Limiting** (`backend/api_server.py`):
- Flask-Limiter added: 10 req/min on `/api/start`, 30 req/min on `/api/chat`
- Closes VULN-01 and VULN-02

**Message length cap corrected:** 2,000 chars (was documented as 5,000 in some files — corrected)

---

## Branch: `main` — POC 1.2 Enhancements

### 2026-03-07 — POC 1.2: Comprehensive Dynamic Guardrails + Multilingual Species Fix

**Comprehensive Dynamic Guardrails** (`enhance/dynamic-guardrails`):
- Created standalone `backend/guardrails.py` module (~415 lines) — OWASP LLM Top 10 coverage
- **8 guardrail categories**, each with compiled regex patterns:
  1. **Prompt injection / jailbreak** (OWASP LLM01, LLM07): ignore instructions, DAN, mode switches, jailbreak, reveal system prompt, inject fake system message, roleplay-as-X, encoded payloads
  2. **Data extraction** (OWASP LLM02): API keys, tokens, credentials, env vars, config file requests
  3. **Violence / weapons**: creating weapons/explosives, terrorism, self-harm, animal cruelty, weapon/ammo terms
  4. **Sexual / explicit**: pornography, bestiality, explicit acts, body parts (non-medical context only), sex toys, solicitation, slurs
  5. **Human-as-pet**: treating humans as animals, leashing/caging humans
  6. **Substance abuse**: giving pets drugs/alcohol (non-medical — "my dog ate marijuana" exempt as medical emergency)
  7. **Abuse / harassment**: directed profanity, threats against bot/staff, slurs (N-word, F-slur, R-word, C-word)
  8. **Trolling / off-topic**: crypto, homework, code writing, conspiracy, dating, gambling, roleplay-as-boyfriend
- **Leet-speak normalization** (`str.maketrans`): `0→o, 1→i, 3→e, 4→a, 5→s, 7→t, 8→b, @→a, $→s, !→i, +→t`
- **Multilingual patterns** for FR, ES, ZH, AR, HI, UR in 6 categories (sexual, violence, abuse, drugs, prompt injection, human-as-pet)
- **Pet-medical context exemption**: legitimate emergencies (e.g. "my dog ate rat poison", "my cat drank antifreeze") bypass violence/substance/sexual categories
- All responses localized in 7 languages via `_GUARDRAIL_STRINGS` (5 new response keys × 7 languages)
- **181-case test suite** (`test_guardrails.py`) covering all 8 categories + leet-speak + multilingual + false-positive prevention
- Integrated into `_pre_intake_screen()` as check #1, before deceased/non-pet/normal-behavior checks

**Multilingual Species Recognition Fix** (`enhance/dynamic-guardrails`):
- Added Hindi, Urdu, Arabic, Chinese, French, Spanish species words to `IntakeAgent._SPECIES_WORDS`
- Added multilingual noise phrases to `IntakeAgent._NOISE_PHRASES`
- Added Hindi, Urdu, Arabic, Chinese species keywords to orchestrator `_species_keywords` fallback
- Fixed: "कुत्ता" (dog), "बिल्ली" (cat) etc. now correctly recognized as species (not treated as complaints)

---

## Branch: `main` — POC 1.1 Enhancements

### 2026-03-07 — POC 1.1: Guardrails, Diagnostic Intake, i18n, Observability, Integrations, UX

**Tag:** `v1.1.0-poc`

**Smart Intake Guardrails** (`enhance/smart-intake-guardrails`):
- Added `_pre_intake_screen()` — deterministic pre-LLM guardrail with 4 categories
- Abuse/threats: firm boundary, never engages
- Deceased pet: compassionate response + grief resources, marks session complete
- Non-pet subjects ("my human isn't well"): gentle redirect to human health services
- Normal animal behavior ("humping"): acknowledge as normal, no medical triage
- Smart false-positive prevention (pet+human co-mention, medical+behavior overlap)
- All responses localized in 7 languages via `_GUARDRAIL_STRINGS`

**Structured Diagnostic Follow-up** (`enhance/structured-intake-questions`):
- After species + chief complaint known, asks timeline → eating/drinking → energy level
- One question per turn, max 3 diagnostic turns, skips already-answered questions
- Species-personalized questions, localized in 7 languages

**Booking Confirmation Fix** (`fix/booking-confirmation`):
- Natural slot matching with score-based system: day name(+2), month(+1), day number(+1), time+ampm(+2), provider(+3), threshold ≥2
- "Tuesday March 10th 11am with Dr. Patel" now books without requiring "book" keyword

**Full Language Enforcement** (`fix/multi-language-enforcement`):
- `_UI_STRINGS` dict: 7 languages × 18 keys for all orchestrator messages
- `_RESTART_KEYWORDS_I18N` / `_BOOK_KEYWORDS_I18N`: per-language keyword sets
- `_t()` helper method for localized string retrieval
- Localized emergency messages, intake fallbacks (`_FALLBACK_ASK_SPECIES`, `_FALLBACK_ASK_SYMPTOMS`)
- Strengthened intake prompt rules 8 + 9 (never guess species)

**LangSmith Observability** (`enhance/langsmith-tracing`):
- `wrap_openai` on all 3 LLM agents (intake, triage, guidance)
- `@traceable` decorator on `orchestrator.process()`
- Opt-in via `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY`
- Added `langsmith` to requirements.txt

**N8N Webhook Integration** (`enhance/n8n-webhook`):
- Fires POST on terminal states (complete/emergency/booked) from `_build_response()`
- Payload: event, session_id, pet_profile, all agent outputs, booked_slot, language, processing_time
- Non-blocking with 5s timeout, failures logged as warnings

**Twilio Click-to-Call** (`enhance/twilio-voice`):
- Backend `/api/call` endpoint using Twilio REST API
- Backend `/api/twilio/status` for frontend feature detection
- Frontend "Call via app" button on vet cards when Twilio is enabled
- Phone number validation (E.164), opt-in via Twilio env vars
- Native `tel:` links still work regardless

**Scroll Bug Fix** (`fix/scroll-bug`):
- Centralized `_scrollToBottom(behavior)` helper: 'smooth' default, 'instant' during typing
- `_isNearBottom()` helper for future user-is-reading detection
- Removed CSS `scroll-behavior: smooth` (now controlled via JS)
- Replaced all 12 raw `scrollTop = scrollHeight` calls

---

## Branch: `PetCare_Syed` on `FergieFeng/petcare-agentic-system`

### 2026-03-06 — Auth middleware, session persistence, deployment readiness, docs update

**Commits:** `docs: update all documentation to match current POC + auth middleware`

**Security & Deployment:**
- Added HTTP Basic Auth middleware to `api_server.py` (credentials from environment variables only — never hardcoded)
- Auth exempts `/api/health`, `manifest.json`, and `service-worker.js`
- Added `AUTH_ENABLED`, `AUTH_USERNAME`, `AUTH_PASSWORD` to `.env.example` (with security warnings)
- Created `backend/__init__.py` for Gunicorn module import support

**Session Persistence:**
- Implemented two-tier session management: active sessions (1hr TTL) + completed sessions (24hr TTL)
- Completed triage sessions preserved for PDF download for 24 hours
- Added background cleanup thread (every 10 minutes) for expired sessions

**Location Fallback:**
- Added manual city/postal code entry when geolocation fails or is denied
- Added OpenStreetMap Nominatim geocoding as fallback for manual location input
- Added default location option (Toronto) for quick testing

**Full Multilingual Output:**
- Updated all UI strings (vet finder, cost estimator, feedback, reminders, breed risks, history, emergency, photo upload, API errors) to use `t()` translation helper
- All 7 languages now have complete UI string coverage

**Documentation:**
- Updated `README.md`: expanded System Architecture diagram (auth, session tiers, Google Places, Nominatim, PWA, notifications), enriched Agent Pipeline Flow (detailed per-agent I/O), expanded Voice Architecture (safety layer), detailed Core Multi-Agent Layer table (inputs/outputs per agent), added auth env vars, updated project structure
- Updated `TECH_STACK.md`: added fpdf2 to dependencies, added auth middleware, two-tier sessions, external API integrations table, updated Docker CMD to gunicorn
- Updated `DEPLOYMENT_GUIDE.md`: added auth env vars to Render and Railway sections with security notes
- Updated `PROJECT_PLAN.md`: marked auth/deploy task as done in Phase 8
- Updated `AGENT_DESIGN_CANVAS.md`: confirmed all enhanced features listed
- Updated this changelog

---

### 2026-03-06 — Frontend redesign + consumer-ready features

**Commits:** `feat: redesign frontend with professional PetCare theme`, plus consumer features

**Frontend Redesign (Phase 8):**
- Complete visual overhaul with warm teal/emerald color palette (#0d9488)
- Gradient header with branded paw logo and backdrop watermark
- Assistant messages now display paw avatar indicators (🐾 in gradient circle)
- Circular send button with SVG arrow icon (replaces text "Send")
- Subtle dot-pattern chat background for visual depth
- Inter font from Google Fonts for modern typography
- Custom scrollbar styling in chat area
- Warm dark mode (teal-tinted, not cold blue-black)
- Updated manifest.json with new theme colors
- All cards (cost estimate, feedback, reminders, breed risk) styled consistently
- RTL support preserved for Arabic/Urdu

**Consumer-Ready Features (Phase 7):**
- **Streaming responses:** Character-by-character text display (ChatGPT-like feel)
- **Consent & privacy banner:** PIPEDA/PHIPA-style consent on first load
- **Cost estimator:** Shows estimated visit costs post-triage ($200-500 emergency, etc.)
- **Feedback rating:** 1-5 star rating with optional comment
- **Follow-up reminders:** Browser notification reminders (1hr, 30min, 1 day, test)
- **Breed-specific risk alerts:** Health risk warnings for 11+ breeds (Golden Retriever, Persian, etc.)
- **Dark mode:** Toggle in header with warm tones
- **PWA support:** Web app manifest + service worker for mobile installation
- **Chat transcript export:** Download full conversation as .txt file
- **Animated onboarding:** 3-step walkthrough for first-time users

**Bug Fixes:**
- Fixed species misidentification (dog vs cat) in Guidance Agent through strengthened LLM prompts
- Expanded species detection to handle all animals (chickens, roosters, horses, reptiles, fish, exotic pets)
- Fixed vet finder geolocation hanging by adding 12-second timeout and better error handling
- Fixed PDF download 404 error by adding graceful session expiry message

**Updated:** `README.md`, `PROJECT_PLAN.md`, `docs/AGENT_DESIGN_CANVAS.md`, `DEPLOYMENT_GUIDE.md`, `TECH_STACK.md`

---

### 2026-03-02 — Baseline methodology from diana-baseline branch

**Commit:** `docs: integrate BASELINE_METHODOLOGY from diana-baseline (author Diana Liu)`

- **Added** `docs/BASELINE_METHODOLOGY.md` from `diana-baseline` branch (author: Diana Liu). Defines **Baseline-1: Manual receptionist phone-call script (non-AI)** — 10-question intake script, manual red-flag review, urgency tier, routing, scheduling. Includes shared test set, gold labels table, evaluation metrics M1–M6, results table template, step-by-step comparison procedure, voice scope (non-blocking for MVP), threats to validity, and evidence artifacts. Used to evaluate the 7-agent system against a realistic status-quo baseline.
- **Updated** `README.md` Documentation table to link to baseline methodology.
- **Updated** `technical_report.md` §4.3 Baseline Comparison to reference the document and Option 1.
- **Updated** `docs/test_scenarios.md` to reference baseline comparison and BASELINE_METHODOLOGY.md.

### 2026-03-02 — Agent Design Canvas (MD) + Diana Liu as contributor

**Commit:** `docs: add Agent Design Canvas as MD (author Diana Liu), add Diana as contributor to design docs`

- **Added** `docs/AGENT_DESIGN_CANVAS.md` — Canonical Agent Design Canvas converted from the Word canvas; author **Diana Liu**. Same format: STEP 1 (Problem Definition), STEP 2 (Core Workflow with Mermaid diagram), STEP 3 (Capabilities & Memory), STEP 4 (Data & Constraints), STEP 5 (Success Criteria & Failure Analysis). Updated to reflect current 7-agent architecture, Flask, Render, voice, multilingual.
- **Added** Diana Liu as **Contributors** on all design docs: `agents.md`, `system_overview.md`, `orchestrator.md`, `data_model.md`, `repo_structure.md`, `output_schema.md`, `scope_and_roles.md`, `workflow_technical.md`, `workflow_non_technical.md`, `CHANGELOG.md`, `DESIGN_COMPARISON.md`, `test_scenarios.md`.
- **Updated** `docs/architecture/README.md` and main `README.md` Documentation table to link to the Agent Design Canvas.

### 2026-03-01 — Repository cleanup (PetCare-only)

**Commit:** `chore: remove resume/job-related and legacy files; PetCare-only repo`

Removed all files not relevant to the PetCare Triage & Smart Booking Agent:

- **Removed** `docs/agent_specs/jd_analysis/`, `resume_profiling/`, `application_strategy/`, `hidden_signal/`, `evidence_citation/`, `hard_match/` — these were from the resume-alignment-engine template; PetCare uses only `intake`, `safety_gate`, `confidence_gate`, `triage`, `routing`, `scheduling`, `guidance_summary`, `orchestrator`.
- **Removed** `src/` — legacy prototype code (Streamlit UI, JD/resume agent stubs). Active code lives in `backend/` and `frontend/`.
- **Removed** `docs/current_version/` — contained Resume Alignment Engine workflow guide; not applicable to PetCare.
- **Removed** empty duplicate directories (`docs/agent_specs 2`, `docs/architecture 2`, etc.).
- **Updated** `README.md` and `docs/architecture/repo_structure.md` to drop references to `src/` and `current_version/`.

### 2026-03-01 — Merge from main + content integration

**Commit:** `docs: integrate main-branch content — data model, test scenarios, voice safety, repo structure`

Compared the `main` branch docs against the `PetCare_Syed` branch and integrated all useful content:

- **Added** `docs/architecture/data_model.md` — Full field-level data schema for all JSON files and in-memory objects, data access policy matrix, privacy/security guidance. Based on main's `data-model.md` but aligned with our actual `clinic_rules.json`, `red_flags.json`, and `available_slots.json`.
- **Added** `docs/test_scenarios.md` — 6 end-to-end test scenarios (emergency, routine, toxin ingestion, ambiguous input, multilingual, voice with noise) with expected agent behavior tables and a validation checklist covering safety, pipeline correctness, output quality, voice, and multilingual.
- **Added** voice safety requirements to `TECH_STACK.md` — Critical field confirmation, red-flag double confirmation, confidence-based fallback, failure scenario table, testing requirements with WER targets. Sourced from main's `voice-extension.md`.
- **Added** data access policy matrix to `docs/architecture/agents.md` — Agent-level read/write permissions for all data stores, responsibility boundary rules for Triage, Scheduling, Safety Gate, and Guidance agents.
- **Added** `docs/architecture/repo_structure.md` — Complete repository layout with directory tree, file descriptions, and design rationale. Replaces main's outdated Google ADK-based structure.
- **Added** `docs/CHANGELOG.md` — This file. Full project history.
- **Preserved** original main-branch docs in `docs/original_main/` for reference.

### 2026-03-01 — Migration to petcare-agentic-system

**Commit:** `feat: migrate PetCare project from resume-alignment-engine`

Migrated the full project from the `PetCare` branch on `FergieFeng/resume-alignment-engine` to the dedicated `FergieFeng/petcare-agentic-system` repository. All repo URL references updated. Original main-branch docs preserved in `docs/original_main/`.

### 2026-03-01 — Custom orchestrator decision documented

**Commit:** `docs: document custom orchestrator decision (no LangGraph/ADK for POC)`

Assessed Google ADK and LangGraph as agent frameworks. Decision: use custom Python orchestrator for POC (simpler, debuggable, meets assignment requirements). LangGraph documented as optional post-POC formalization. Google ADK not recommended (Vertex AI–centric). Updated: `PROJECT_PLAN.md`, `TECH_STACK.md`, `technical_report.md`, `docs/architecture/orchestrator.md`, `docs/architecture/system_overview.md`.

### 2026-03-01 — Mermaid diagram cleanup

**Commits:** `fix: rewrite mermaid diagrams for clean GitHub rendering` (x2)

Rewrote all 4 mermaid diagrams in `README.md` for reliable GitHub rendering: flattened deep nesting, used node-to-node edges instead of cross-subgraph edges, shortened labels, added color coding. Diagrams: System Architecture, Agent Pipeline Flow, Voice Architecture, Deployment Roadmap.

### 2026-03-01 — n8n workflow automation integration

**Commit:** `feat: integrate n8n workflow automation as actions layer`

Added n8n as a post-intake actions layer. Created `docker-compose.yml` (petcare-agent + n8n containers). Defined 5 n8n workflows (Emergency Alert, Clinic Summary Delivery, Appointment Confirmation, Analytics Logger, Follow-Up Reminder). Added Phase 4 to `PROJECT_PLAN.md`. Updated `TECH_STACK.md`, `README.md`, `.env.example`.

### 2026-03-01 — Mermaid architecture diagrams + MMAI 891 update

**Commit:** `feat: add mermaid architecture diagrams, update to MMAI 891`

Replaced static PNG reference with 4 comprehensive mermaid diagrams in `README.md`. Updated all references from "MMAI 2026 Capstone" to "MMAI 891 Final Project" across all files.

### 2026-03-01 — Multilingual support (7 languages + RTL)

**Commit:** `feat: add multilingual support — 7 languages with RTL`

Added support for English, French, Chinese (Mandarin), Arabic, Spanish, Hindi, and Urdu. Frontend: language selector dropdown, translated UI strings, RTL layout for Arabic/Urdu. Backend: language-aware session management, Whisper language hints, multilingual welcome messages. Updated: `frontend/index.html`, `frontend/js/app.js`, `frontend/styles/main.css`, `backend/api_server.py`.

### 2026-03-01 — Deployment guide + tech stack rewrite

**Commit:** `feat: add deployment guide, rewrite tech stack with runtime architecture`

Created `DEPLOYMENT_GUIDE.md` with step-by-step instructions for Local Python, Docker, Render, and Railway. Rewrote `TECH_STACK.md` with runtime architecture diagrams, agent execution flow, Docker container details, and cost estimates.

### 2026-03-01 — Voice support (3 tiers) + code comments

**Commit:** `feat: add voice support (3 tiers), detailed code comments, TECH_STACK.md`

Implemented 3-tier voice support: Tier 1 (browser Web Speech API), Tier 2 (OpenAI Whisper STT + TTS), Tier 3 (Realtime API — stretch goal). Added voice endpoints to API server. Added detailed code comments with author attribution across all backend and frontend files. Created `TECH_STACK.md`.

### 2026-03-01 — Architecture diagram, data sources, Docker setup

**Commit:** `feat: add author info, architecture diagram, data sources, Docker setup`

Added author (Syed Ali Turab) and date (March 1, 2026) to all files. Created architecture workflow diagram. Documented 4 external data sources. Created `Dockerfile`, `start.sh`, `start.ps1`, `.env.example`. Added `DEPLOYMENT_GUIDE.md` link structure.

### 2026-03-01 — Initial project scaffolding

**Commit:** `feat: add PetCare Triage & Smart Booking Agent project scaffolding`

Created the full project structure: `backend/` (Flask API, orchestrator, 7 agent stubs), `frontend/` (chat UI), `docs/` (architecture, agent specs), data files (`clinic_rules.json`, `red_flags.json`, `available_slots.json`), `README.md`, `PROJECT_PLAN.md`, `requirements.txt`.

---

## Branch: `main` (original repo content)

### 2026-02-28 — Initial documentation

**Commit:** `Initialize project documentation`

Created foundational docs: `README.md`, `docs/architecture.md`, `docs/agent-design.md`, `docs/data-model.md`, `docs/voice-extension.md`, `docs/workflow-use-cases.md`, `docs/repo-structure.md`, `docs/changelog.md`. No implementation code — documentation-only commit establishing the system design.

---

## Reading Order for New Developers

1. `README.md` — Project purpose, architecture diagrams, quick start
2. `docs/architecture/system_overview.md` — System layers, tech stack, workflow
3. `docs/test_scenarios.md` — Concrete end-to-end test cases
4. `docs/architecture/agents.md` — Agent responsibilities, I/O contracts, data access
5. `docs/architecture/data_model.md` — Data schemas, field specs, privacy
6. `docs/architecture/orchestrator.md` — Workflow control, branching, safety rules
7. `docs/architecture/repo_structure.md` — Repository layout and design rationale
8. `TECH_STACK.md` — Full technology details, Docker, deployment
9. `PROJECT_PLAN.md` — Development roadmap, phases, risk register

---

## Handoff Notes

- Active development branch: `main`
- All work has been merged to `main`
- The `docs/original_main/` folder preserves all main-branch docs for reference
- Active code is in `backend/` and `frontend/` only (legacy `src/` and resume/job-related specs were removed in repo cleanup)
- Keep this changelog updated when adding new features or docs

---

End of Changelog
