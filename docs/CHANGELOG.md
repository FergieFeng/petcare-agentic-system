# Changelog

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview | **Date:** March 1, 2026

---

## Purpose

This file tracks the evolution of the PetCare Triage & Smart Booking Agent project. It serves as a handoff document for collaborators and a quick reference for what has been built, when, and in what order.

---

## fix/ux-bugs-03-04 — UX Bug Fixes — 2026-03-08

**Tag:** `fix/ux-bugs-03-04-v1.0`

### BUG-03 — Social / Greeting Input (no longer re-asks the same question)
- Added `_SOCIAL_PATTERNS` (compiled regexes) and `_NAME_FROM_GREETING_RE` at module level in `backend/orchestrator.py`
- New `_is_social_input(text)` method: returns `True` when the message contains a social greeting with no pet or symptom content; checks against `_PET_OR_SYMPTOM_WORDS_RE` (multilingual) to avoid false positives
- New `_extract_owner_name(text)` method: parses "Hello, this is Diana" / "my name is X" to extract and store the owner's first name in `session.pet_profile.owner_name`
- In `Orchestrator.process()`, social messages are intercepted BEFORE calling the intake agent — system responds with a warm personalized greeting and redirects to the CURRENT unanswered question (species → `social_redirect_no_species`; complaint → `social_redirect_has_species`) without incrementing `clarification_count`
- New i18n keys `social_redirect_no_species` and `social_redirect_has_species` added in all 7 languages (EN/FR/ES/ZH/AR/HI/UR)

### BUG-04 — Duration Extraction (inline timeline no longer ignored)
- Added `_DURATION_RE` compiled regex at module level in `backend/orchestrator.py` — matches: "for last 3 days", "since yesterday", "started this morning", "about a week", "over the past 2 hours", etc.
- In `Orchestrator.process()`, `_DURATION_RE` is applied to every incoming message BEFORE the LLM intake call; if a duration phrase is found and `symptoms.timeline` is empty, it is pre-populated — the LLM then inherits this context and skips asking for timeline
- `enrich_context()` already gates on `has_timeline = bool(symptoms.get('timeline'))`, so the pre-extracted value prevents both the LLM intake and the enrichment agent from re-asking duration
- Strengthened LLM system prompt in `intake_agent.py` (TIMELINE EXTRACTION section): added 8 explicit extraction examples ("for last 3 days" → timeline: "3 days", etc.) and bold instruction: "do NOT ask for duration if it is already present in the message"

### BUG-01 — Confidence Gate Loop Cap (max 2 attempts, independent counter)
- Confidence gate section in `Orchestrator.process()` now uses `session['confidence_clarify_count']` instead of the shared `session['clarification_count']` — prevents the intake-loop reset (`clarification_count = 0` on intake complete) from also resetting the confidence gate counter, which previously allowed unlimited confidence-gate loops
- `confidence_clarify_count` is reset to 0 when the gate finally routes to receptionist, so a fresh session works correctly

### BUG-02 — Tone Inconsistency Post-Triage
- **Don't tips rendered:** `guidance['dont']` bullets are now included in the final assembled message (was entirely missing before), introduced with `dont_do` i18n key (up to 2 tips, prefixed with `✗`)
- **Section headers warmer:** `available_appointments`, `while_you_wait`, `dont_do`, and `seek_emergency_if` strings updated in all 7 languages to read more like a caring friend than a clinical form (e.g. "I found a few appointment options that should work:" instead of "Here are some appointment options for you:")
- **Pet name personalization:** `pet_ref` variable built from `pet_profile.pet_name` if captured, falling back to "your {species}"

---

## Branches: Post-v1.0 Improvement Passes — 2026-03-08

### improve/scheduling-urgency-window · improve/slot-confirmation · improve/session-state-enum · improve/frontend-ux

**Tag:** `improve/post-v1.0`

**Scheduling Agent — Urgency Date-Window Filtering (`improve/scheduling-urgency-window`):**
- Scheduling Agent now filters available slots by a date window matched to the urgency tier: Same-day → today only, Soon → next 1–3 days, Routine → next 7 days
- Falls back to the full slot pool if the strict window yields no matching slots, preventing empty proposals
- File: `backend/agents/scheduling_agent.py` / `backend/orchestrator.py`

**Slot Confirmation — Multilingual Ordinal + Day-Name Matching (`improve/slot-confirmation`):**
- `_match_slot()` in `backend/orchestrator.py` now recognises ordinal words in all 7 languages when owners select a slot by position: EN ("first"/"second"), FR ("premier"/"deuxième"), ES ("primero"/"segundo"), ZH ("第一个"/"第二个"), AR ("الأول"/"الثاني"), HI ("पहला"/"दूसरा"), UR ("پہلا"/"دوسرا")
- Day-name matching extended to all 7 languages via new `_DAY_NAMES` dict — previously relied on Python `strftime('%A')` (English only)
- Removed redundant `import re` statement inside the method

**Session State Constants — `SessionState` Class (`improve/session-state-enum`):**
- Added `SessionState` class to `backend/orchestrator.py` with named constants: `INTAKE`, `COMPLETE`, `EMERGENCY`, `BOOKED`, and the `TERMINAL_STATES` set
- All session state assignments and checks in the Orchestrator now use these constants instead of raw strings, eliminating silent typo bugs
- Removed unreachable dead code block in `backend/agents/intake_agent.py` — lines after `return None` inside `enrich_context()` except block that could never execute

**Frontend UX Improvements (`improve/frontend-ux`):**
- **Auto-grow textarea:** input box expands as the owner types (up to 200 px max-height) and shrinks back when text is deleted
- **Live character counter:** displays "{count} / 2000"; turns amber at 80% of the limit (1600 chars), red at the limit (2000 chars); hard cap enforced — characters beyond the limit are rejected
- **Emergency banner dark-mode fix:** banner now uses CSS class `.emergency-banner-bar` instead of inline `style.cssText`, which was overriding dark-mode styles
- **`AbortController` for `/message` fetch:** cancels any in-flight request before sending a new one — prevents double-submission race conditions
- **Hardcoded English strings localised:** "Session expired. Reconnecting..." → `t('sessionExpired')`; "Get Started" → `t('getStarted')`; new i18n keys `sessionExpired`, `getStarted`, and `charCount` added to all 7 language blocks
- **Accessibility — `aria-label` on icon-only buttons:** voice, photo, send, TTS, and dark-mode toggle buttons now carry `aria-label`; voice and TTS buttons update their label dynamically when toggled

---

## Branch: `main` — Production Readiness Pass

### 2026-03-08 — Adaptive Intake + Retry + Temporal Safety Gate + Triage Context

**Tag:** `prod/readiness-v1.0`

**Adaptive Context Enrichment (replaces rigid 3-question diagnostic loop):**
- Removed hardcoded timeline→eating→energy questioning script from `orchestrator.py`
- New `IntakeAgent.enrich_context()` method (`backend/agents/intake_agent.py`) calls GPT-4o-mini to generate ONE complaint-specific follow-up question per turn
- Examples: limping dog → "when did you first notice it?"; vomiting cat → "is she still keeping water down?"; routine checkup → SKIP (no question asked)
- Capped at `MAX_ENRICHMENT_TURNS = 2` per session — conversation never exceeds 2 context-gathering turns
- Decorated with `@traceable(name="intake.enrich_context", tags=["intake", "enrichment"])` for LangSmith visibility
- Supports all 7 languages (lang_name passed to LLM prompt)

**Scheduling Agent — Fresh Slots Per Request:**
- `SchedulingAgent.__init__()` no longer generates mock slots at startup
- `_generate_mock_slots()` called fresh inside `process()` on every request
- Proposed appointment dates are now always relative to the current date, never stale

**Triage Agent — Breed / Age / Weight Context:**
- `orchestrator.py` now passes `pet_profile=self.session.get('pet_profile', {})` to `triage_agent.process()`
- `TriageAgent.process()` extracts `breed`, `age`, `weight` from `pet_profile` and includes them in the LLM user message
- New age-based urgency rule in system prompt: geriatric (>8 yrs dog, >10 yrs cat) or very young (<6 months) → one tier higher when borderline
- File: `backend/agents/triage_agent.py`

**Safety Gate — Multilingual Temporal Past-Incident Filter:**
- New `_is_past_incident(text, flag)` function scans ±80-char window around each flag match
- If temporal past markers found near the match, the flag is skipped (not escalated)
- Prevents false escalations for descriptions like "my dog ate chocolate last year" or "she had a seizure before, but now she just has a limp"
- Temporal markers cover all 7 languages: EN / FR / ES / ZH / AR / HI / UR
- File: `backend/agents/safety_gate_agent.py`

**LLM Retry Wrapper — `backend/utils/llm_utils.py` (new file):**
- Shared `llm_call_with_retry()` with exponential backoff (base 1.5s, doubles per attempt, default 3 retries)
- Covers: `RateLimitError`, `APIConnectionError`, `APITimeoutError`, `InternalServerError`
- Non-retryable errors raise immediately; reduces agent failures due to transient OpenAI outages
- Wired into: `intake_agent.py` (both LLM calls), `triage_agent.py`, `guidance_summary.py`

---

## Branch: `security/guardrail-pentest-v2` → `main` — Pentest #2 + Bug Fixes + Exotic Species Tests

### 2026-03-08 — Guardrail Red Team Pentest #2 + BUG-01 + BUG-02 + Exotic Species

**Tag:** `security/pentest-v2.0`

**Pentest #2 — 85-Test Guardrail Red Team:**
- Automated script `backend/guardrail_pentest_v2.py`: 10 attack vectors × 7 languages (70 tests) + 15 edge-case probes
- **Result: 0 bypasses across all 85 tests** — 100% pass rate
- Full report: `backend/guardrail_pentest_report.md`
- Three-layer defence confirmed: Stage 1 regex (44 blocks) + Stage 2 LLM classifier + intake agent safety (26 safe handles)
- Fixed false-positive in bypass detection logic (`'triage'` removed from `BYPASS_SYSTEMPROMPT`; guardrail-block check now runs before bypass scan)
- Pentest script credentials: env vars only (`PETCARE_AUTH_USER`, `PETCARE_AUTH_PASS`) — never hardcoded

**BUG-01 — Confidence Gate Infinite Loop (fixed):**
- Symptom: "How long has this been going on?" asked up to 3 times for vague answers
- Root cause: `diagnostic_step` counter did not track per-field asks; timeline could be re-asked on every turn until cap
- Fix: Added `diag_asked` set to `orchestrator.py`; each field asked at most once; "unknown" accepted on second attempt
- File: `backend/orchestrator.py`

**BUG-02 — Robotic Post-Triage Tone (fixed):**
- Symptom: Intake agent warm and conversational, but triage output opened with "Based on what you've told me…"
- Root cause: Hardcoded `recommend_visit` template; guidance agent LLM prompt lacked tone instructions
- Fix: Warmer `recommend_visit` openers in all 7 languages; explicit TONE section added to guidance agent system prompt
- Files: `backend/orchestrator.py`, `backend/agents/guidance_summary.py`

**Exotic Species Coverage Confirmed + Test Cases Added:**
- Verified: alligator, snake, bird, hamster all accepted and processed correctly — pipeline never crashes for unusual species
- 4 new test cases added to `testcases.md` (TC-EX01 through TC-EX04)
- Total test cases: 34 (up from 30)

**Documentation Updates:**
- `docs/SECURITY_AUDIT.md`: New §9 Pentest #2 with full summary, vector table, residual observations, bug-fix table
- `docs/CHANGELOG.md`: This entry
- `testcases.md`: Exotic species section + results summary updated

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
