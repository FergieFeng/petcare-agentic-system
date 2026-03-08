# Agent Design Canvas — PetCare Triage & Smart Booking Agent

**Author:** Diana Liu | **Contributors:** Syed Ali Turab, Fergie Feng | **Team:** Broadview | **Date:** March 6, 2026

This document is the canonical Agent Design Canvas for the PetCare POC, converted to Markdown and updated to reflect the implemented 7-agent architecture, orchestrator, and deployment choices (Flask, Render, voice, multilingual). Original canvas format preserved.

---

## STEP 1: Problem Definition and Agent Justification

### Problem Description

**What specific user task are we solving, improving, or automating?**

Reduce front-desk workload and improve clinical routing by automating pet symptom intake, triage urgency classification, appointment booking support, and vet-facing summary — while providing safe, non-diagnostic “do/don’t” guidance for owners during wait time.

### How is the task done now?

Owners call the clinic; reception staff ask ad-hoc questions, interpret urgency, choose an appointment slot, and manually explain next steps. Intake quality varies by staff experience; peak-time calls create queues; mis-routing (wrong appointment type/doctor/urgency) leads to rescheduling and delays.

### Who is the primary user?

- **Primary:** Clinic receptionist / intake staff (operational user)
- **Secondary:** Pet owners (self-serve intake + scheduling via chat or voice, 7 languages)
- **Downstream:** Veterinarians / vet techs (receive structured intake summary)

### Why does this task require an agent (vs prompting, rules-only, dashboard, classical NLP)?

The workflow is multi-step, branching, and interactive:

- Ask follow-up questions **conditionally** (depends on symptoms and species)
- Identify red flags and **escalate safely** (deterministic Safety Gate before any triage)
- Route case type (e.g. GI, derm, respiratory, injury/pain) and urgency
- Produce **structured handoff summary** for the clinical team

A static prompt is brittle for routing logic and uncertainty handling; rule-based intake alone is too rigid for messy owner descriptions. The design emphasizes an agent as a **structured decision system with escalation rules**, not “a chatbot.”

### What business decision/action/outcome will this agent influence if adopted?

- Faster intake and reduced call burden
- More consistent triage and scheduling accuracy (fewer mis-bookings / rework)
- Better prep for vets (structured case notes before the visit)
- Improved owner experience (clear next steps, less anxiety-driven repeat calls)

### Implementation approach

PetCare is implemented as an **orchestrator agent** that coordinates **seven specialized sub-agents**: Intake (A), Safety Gate (B), Confidence Gate (C), Triage (D), Routing (E), Scheduling (F), Guidance & Summary (G). This modular design improves safety, testability, and reliability, especially for high-stakes triage decisions. Backend: Flask; deployment: **Render** (recommended).

**MVP scope (text-first; voice deferred):** Ship the MVP with **text-based chat first**. Interactive voice is harder to build and test; with limited time, a broken or unstable voice feature would hurt the demo more than help. The assignment rewards a **clean working pipeline with solid test results**, not extra features. Voice can be added as a **bonus** later if capacity allows; do not depend on it for the core demo or baseline comparison. Multilingual (7 languages) is supported for text; voice tiers remain optional/stretch.

---

## STEP 2: Core Workflow Abstraction

### Trigger event

A pet owner initiates intake via **web chat** (or voice-to-text) in one of 7 languages (English, French, Chinese, Arabic, Spanish, Hindi, Urdu). The frontend calls the Flask API; the Orchestrator receives the message and runs the pipeline.

### End-to-end workflow (Mermaid)

```mermaid
flowchart TD
    TRIGGER(["Owner sends message"])
    TRIGGER --> A["A · Intake"]
    A --> A_Q{"Intake complete?"}
    A_Q -->|No| FOLLOW["Return follow-up question"]
    FOLLOW --> TRIGGER
    A_Q -->|Yes| B["B · Safety Gate"]
    B --> B_Q{"Red flag detected?"}
    B_Q -->|Yes| EM["Emergency path"]
    EM --> G_EM["G · Guidance (emergency)"]
    G_EM --> OUT_EM["Owner: seek emergency care now"]
    B_Q -->|No| C["C · Confidence Gate"]
    C --> C_Q{"Proceed?"}
    C_Q -->|Clarify| CLARIFY["Ask missing fields"]
    CLARIFY --> TRIGGER
    C_Q -->|Human review| HR["Route to receptionist"]
    C_Q -->|Proceed| D["D · Triage"]
    D --> E["E · Routing"]
    E --> F["F · Scheduling"]
    F --> G["G · Guidance + Summary"]
    G --> OUT["Owner: urgency + guidance + slots\nClinic: structured JSON"]
```

### Major processing steps

| Step | Sub-Agent | Responsibility |
|------|-----------|----------------|
| 1 | **A — Intake** | Collect pet profile + chief complaint + timeline; ask adaptive follow-ups by symptom area (GI, respiratory, derm, injury, urinary, neurological, behavioral). |
| 2 | **B — Safety Gate** | Rule-based red-flag detection → immediate escalation messaging; **stop booking flow**. |
| 3 | **C — Confidence Gate** | Verify required fields and confidence; if low → clarify (loop back to Intake, max 2×) or route to receptionist review. |
| 4 | **D — Triage** | Assign urgency tier (Emergency / Same-day / Soon / Routine) with rationale + confidence. |
| 5 | **E — Routing** | Classify symptom category; map to appointment type / provider pool (clinic rule map). |
| 6 | **F — Scheduling** | Propose available slots or generate booking request payload. |
| 7 | **G — Guidance + Summary** | Owner “do/don’t while waiting” + escalation cues; clinic-ready structured intake summary (JSON). |

### Branching conditions / decision rules

- **Emergency escalation** if red flags present (e.g. difficulty breathing, uncontrolled bleeding, suspected toxin ingestion, seizures, collapse, inability to urinate). Pipeline short-circuits to Guidance with emergency-specific output; no triage/routing/booking.
- **Low confidence or missing critical fields** → ask clarifying questions (max 2 loops) or route to receptionist review.
- **Species-specific routing** (cat vs dog vs exotic) → different question sets and provider pool (from `clinic_rules.json`).

### Output format

- **Owner-facing:** Urgency level + what happens next + appointment confirmation/request + safe do/don’t guidance (in session language).
- **Clinic-facing (structured JSON):** Pet profile, symptom timeline, triage tier, red flags, suggested category, confidence score, notes. Always English.

### Autonomy boundaries (act vs escalate)

| The agent **can** | The agent **cannot** |
|-------------------|----------------------|
| Intake, triage tier suggestion, routing suggestion, booking request, safe general guidance, clinic summary | Give a diagnosis; prescribe meds/dosing; override clinic policy; finalize emergency decisions without required escalation messaging |
| **Escalate to human** when confidence is low, red flags appear, or owner responses conflict (e.g. “not breathing” + “acting normal”). | |

---

## STEP 3: Capabilities and Memory Design

### Capabilities needed

| Agent | Capability |
|-------|------------|
| A — Intake | Adaptive questioning + structured extraction (LLM). |
| B — Safety Gate | Rule-based red-flag detection + escalation response (rules + `red_flags.json`). |
| C — Confidence Gate | Required-field validation + uncertainty handling + loop logic (rules). |
| D — Triage | Urgency classification + confidence scoring (LLM + rules). |
| E — Routing | Symptom category → appointment type / provider mapping (rules + `clinic_rules.json`). |
| F — Scheduling | Slot proposal / booking request creation (rules + `available_slots.json`). |
| G — Guidance/Summary | Safe waiting guidance + structured clinic handoff note (LLM). |

### Tools / external systems

**MVP (current):**

- Clinic rulebook (triage + routing) → `backend/data/clinic_rules.json`
- Red-flag list → `backend/data/red_flags.json`
- Mock schedule → `backend/data/available_slots.json`
- Optional: n8n webhooks for post-intake actions (email, Slack, Google Sheets)

**Enhanced features (v1.1-poc):**

- Google Places API (New) → nearby vet finder (real clinics, ratings, phone, directions, calling)
- OpenAI Vision → photo symptom analysis (visual observation, never diagnoses)
- fpdf2 → downloadable PDF triage summary (clinic-ready format with branding)
- Browser localStorage → pet profile persistence and symptom history tracking
- Post-triage appointment booking flow (confirm by name or ordinal)
- Streaming responses → ChatGPT-like word-by-word display
- Cost estimator → Post-triage visit cost estimates
- Feedback rating → 1-5 star rating with optional comment
- Follow-up reminders → Browser notification reminders
- Breed-specific risk alerts → Health risk warnings for known breeds
- Dark mode → Toggle for accessibility
- PWA support → Install as mobile app (manifest + service worker)
- Chat transcript export → Download full conversation as text
- Animated onboarding → 3-step walkthrough for first-time users

**Frontend design:**
- Warm teal/emerald color palette (#0d9488 primary)
- Gradient header with branded paw logo
- Assistant messages with paw avatar indicators
- Circular send button with SVG arrow icon
- Subtle dot-pattern chat background
- Inter font from Google Fonts
- Responsive design with RTL support
- Warm dark mode (not cold blue-black)

**Later integrations:**

- Scheduling system API (clinic booking platform)
- CRM/EMR; SMS/email notifications

### Respond under uncertainty

- Show confidence score and “needs review” flag when applicable.
- Ask targeted follow-ups when key info missing (duration, severity, eating/drinking, breathing).
- **Default to safer action:** “contact clinic / emergency” when red flags or ambiguity appear.

### Memory strategy

- **Two-tier session store** (server-side, in-memory):
  - `sessions` — active intake sessions (1-hour TTL). Holds `pet_profile`, `symptoms`, `timeline`, `red_flags`, `triage_tier`, `routing`, `booking_request`, `confidence`, full message history, and all agent outputs.
  - `completed_sessions` — finished triages (24-hour TTL). Preserves session data for PDF download window.
  - Background cleanup thread purges expired sessions every 10 minutes.
  - Session count capped at 10,000; per-session message limit of 100.
- **Single-worker Gunicorn** (`--workers 1 --threads 4`): required because sessions are in-memory. Multiple workers would partition sessions across processes, causing session loss.
- **Client-side persistence** (optional): Pet profiles and symptom history stored in browser `localStorage` for returning users. No PII sent to server; user can clear anytime. All localStorage data is HTML-escaped before DOM rendering to prevent stored XSS.
- **No long-term storage** of identifying info by default (privacy-by-design); optional anonymized logs for evaluation.
- Do not store owner identity, phone, or sensitive notes beyond what is needed for the appointment request.

---

## STEP 4: Data Requirements and Operational Constraints

### Data sources required

- Clinic-defined triage rules + red flags + routing policy → `clinic_rules.json`, `red_flags.json`
- Appointment availability → `available_slots.json` (mock for POC)
- Optional for evaluation: anonymized historical intake notes + outcomes (triage vs actual urgency)

### Who owns data / MVP accessibility

- Clinic operations owns scheduling and intake scripts.
- For MVP, synthetic scenarios + small policy/rule doc (no real PHI/pet-owner data).

### Minimum data quality needed

- Routing rules explicit and versioned (avoid “it depends” policies).
- Availability schedule current (or clearly mock).
- Test scenarios cover common + urgent presentations (see `docs/test_scenarios.md`).

### Update frequency

- Schedule: real-time or daily refresh (production); mock for POC.
- Clinic triage/routing policy: quarterly or as clinic changes staffing/services.

### Operational constraints

- **Latency target:** &lt; 10–15 seconds for full intake summary (intake itself is interactive).
- **Cost control:** Limit LLM calls to Intake (A), Triage (D), Guidance (G); B, C, E, F are rule-based.
- **Safety:** Strict non-diagnostic language + red-flag escalation + comprehensive content-safety guardrails (8 categories, OWASP LLM Top 10); logging for audit.
- **Privacy:** Avoid storing sensitive details; minimize retention.
- **Deployment:** Render (recommended) for POC; Docker for local/reproducible runs.

### Security hardening (implemented March 6, 2026)

The POC implements defense-in-depth across all layers:

**Authentication & access control:**
- HTTP Basic Auth on the page entry point (`/`); credentials read exclusively from environment variables (`AUTH_USERNAME`, `AUTH_PASSWORD`), never hardcoded
- API endpoints (`/api/*`) exempt from per-request auth — only reachable from the already-authenticated frontend
- Auth is fail-closed: if env vars are empty, `_check_auth()` always returns `False`

**Input validation (api_server.py):**

| Control | Value | Purpose |
|---------|-------|---------|
| `MAX_CONTENT_LENGTH` | 16 MB | Prevents memory exhaustion via large uploads |
| Message length cap | 2,000 chars | Limits LLM token burn per request |
| Session message cap | 100 messages | Prevents unbounded conversation history |
| Session count cap | 10,000 | Prevents DoS via session flooding |
| Photo MIME allowlist | JPEG, PNG, WebP, GIF | Blocks arbitrary file uploads |
| Audio MIME allowlist | WebM, WAV, MPEG, OGG, MP4 | Blocks arbitrary file uploads |
| TTS voice allowlist | alloy, echo, fable, onyx, nova, shimmer | Prevents invalid API calls |
| Lat/lng range check | ±90° / ±180° | Validates geolocation input |
| PDF filename sanitization | Alphanumeric only, 20 char max | Prevents path traversal in `Content-Disposition` |

**Prompt injection mitigation (intake_agent.py, guidance_summary.py):**
- `_sanitize_for_prompt()` strips control characters (`\x00-\x1f`, `\x7f`) and enforces length limits before any user-derived value is interpolated into an LLM system prompt
- `species` sanitized to 50 chars; `chief_complaint` to 200 chars
- `symptom_area` validated against a fixed allowlist (gastrointestinal, respiratory, dermatological, injury, urinary) — rejects anything else
- Photo analysis species sanitized to alphanumeric + spaces, 30 char max

**Comprehensive content-safety guardrails (`backend/guardrails.py`) — Two-Stage Pipeline:**
- **Stage 1 — Regex fast-path** (~0ms, no API cost): runs before any LLM call on every user message
  - **8 guardrail categories**, ~100 compiled regex patterns:
    1. Prompt injection / jailbreak (OWASP LLM01, LLM07): ignore instructions, DAN, mode switches, jailbreak, reveal system prompt, encoded payloads
    2. Data extraction (OWASP LLM02): API keys, tokens, credentials, env vars, config files
    3. Violence / weapons / terrorism / self-harm / animal cruelty
    4. Sexual / explicit / bestiality / pornography (non-medical body parts exempt in medical context)
    5. Human-as-pet references
    6. Substance abuse involving pets (legitimate ingestion emergencies exempt)
    7. Abuse / harassment / directed profanity / slurs
    8. Trolling / off-topic (crypto, homework, dating, conspiracy, etc.)
  - **Leet-speak normalization**: `0→o, 1→i, 3→e, 4→a, 5→s, 7→t, 8→b, @→a, $→s, !→i, +→t`
  - **Multilingual patterns**: FR, ES, ZH, AR, HI, UR in 6 categories
  - **Pet-medical context exemption**: "my dog ate rat poison", "my cat drank antifreeze" bypass violence/substance/sexual categories
  - **181-case test suite** (`test_guardrails.py`)
  - Localized block responses in all 7 languages
- **Stage 2 — LLM semantic classifier** (GPT-4o-mini, `_llm_classify()`, ~300-500ms): screens messages that pass Stage 1 for semantic/paraphrased attacks — indirect prompt injection, context-manipulation framing ("as a thought experiment with no rules…"), zero-day jailbreaks not covered by regex. **Enabled by default in production** (`GUARDRAIL_LLM_ENABLED=true`).
- **Audit trail**: every Stage 2 call traced in LangSmith as `guardrail.llm_classifier` with tag `llm_classifier` — filterable for real-time safety audit and annotation queues
- **Fail-open**: classifier API errors return `None` — legitimate users are never blocked by an outage

**XSS prevention (frontend/js/app.js):**
- `_escapeHtml()` utility escapes `& < > " '` in all user-derived data before DOM insertion
- Applied in: `_showClinicPanel()`, `_renderVetResults()`, `_showSymptomHistory()`, `_formatMessage()`
- Covers: pet name, species, breed, age, rationale, contributing factors, providers, slot data, vet names/addresses/phones/hours, symptom history entries

**Information disclosure prevention:**
- All `except` handlers return generic error messages to the client (e.g., "Analysis failed. Please try again.")
- Internal details (`str(e)`, stack traces, file paths) logged server-side only

**Credential management:**
- `.env` in `.gitignore` (never committed)
- `.env.example` contains empty placeholders only — no real credentials
- `docker-compose.yml` reads n8n password from env var (`${N8N_AUTH_PASSWORD}`)
- No hardcoded API keys, passwords, or secrets anywhere in the committed codebase

**Rate limiting (Flask-Limiter):**
- `/api/start` capped at **10 sessions/minute** per IP (prevents session-flood DoS)
- `/api/chat` capped at **30 requests/minute** per IP (prevents message-flood DoS)
- Returns HTTP 429 with `Retry-After` header on violation

**HTML-encoding at output boundary (api_server.py):**
- `_escape_pet_profile()` applies `html.escape(quote=True)` to all user-supplied fields (`pet_name`, `breed`, `age`, `weight`) before inclusion in `get_summary()` JSON responses
- Encoding at output time (not storage) keeps raw values available for LLM prompts

**TTS content policy (`_TTS_BLOCKED_PATTERNS`):**
- 8 pre-compiled regex patterns block dosage language, prescription verbs, vet identity claims, named diagnoses, and named antidotes from being synthesized as voice output
- Returns HTTP 400 if content policy violated; no TTS call made

**Not applicable / out of scope for POC:**
- SQL injection: no SQL database (JSON files only; `json.loads()` for parsing)
- CSRF: not applicable (no cookie-based session auth; API is stateless with session ID in URL)

---

## STEP 5: Success Criteria and Failure Analysis

### How to measure success (MVP metrics)

We compare the **agent** against a **manual receptionist phone-script baseline** (same test scenarios). See `docs/BASELINE_METHODOLOGY.md` for the full procedure. Practically, we measure the same four dimensions for both baseline and agent:

| Metric | Baseline (e.g. phone script) | Agent target |
|--------|------------------------------|--------------|
| **Time to complete intake** | e.g. 5 min | e.g. 2 min (target ≥30% reduction) |
| **Required fields captured** | e.g. 70% | **Target >90%** |
| **Triage accuracy** | e.g. inconsistent | **Target >80%** (vs gold labels) |
| **Red-flag detection** | e.g. depends on staff | **Target 100%** (zero missed emergencies) |

**Quality metrics (detail):**

- Triage tier agreement rate with gold labels (target ≥ 80% on test set)
- Routing accuracy to correct appointment type / provider pool (target ≥ 80%)
- Intake completeness — % required fields captured (target ≥ 90%)

**Operational metrics:**

- Reduction in intake time per case vs baseline (target 30%+)
- Reduction in re-bookings / mis-bookings (target 20%+ in pilot)

**Safety:**

- Red-flag detection rate: 100% (zero missed emergencies in test scenarios).

### Potential value (back-of-the-envelope)

Example clinic: 30 calls/day × 5 min intake = 150 min/day. If agent reduces intake by 2 min for half of calls (15 calls): 30 min/day saved ≈ 10 hours/month. At $25/hour admin cost → ~$250/month per clinic, plus softer benefits (better routing, fewer repeat calls).

### Range of uncertainty

Depends on call volume, adoption, and how much scheduling integration exists (large swing if fully integrated vs “draft request”).

### How business impact is validated

Run a 4–6 week pilot: compare average intake time, repeat calls, and re-book rates pre/post; staff survey on intake quality and workload.

### Critical assumptions

- Clinic triage/routing rules can be made explicit enough for an MVP (even if simplified).
- Owners will tolerate structured questions if it’s faster than waiting on hold.

### Three common failure modes

| Failure mode | Description |
|--------------|-------------|
| **Under-triage** | Serious case labeled routine → delayed care. |
| **Over-triage** | Too many cases flagged urgent → overload and loss of trust. |
| **Bad routing** | Wrong appointment type/provider → rescheduling and delay. |

### Mitigations

- **Under-triage:** Conservative red-flag rules + mandatory escalation messaging; Safety Gate runs before triage.
- **Over-triage:** Calibrate thresholds using scenario tests; allow receptionist override; document in report.
- **Bad routing:** Clinic-owned routing map in version control (`clinic_rules.json`); track override reasons and refine rules.

---

## STEP 6: Security Pentest Results (March 2026)

### Traditional Web Vulnerability Pentest

A black-box OSCP-style pentest was conducted against the live Render deployment (`https://petcare-agentic-system.onrender.com`) using `backend/security_pentest.py`. Results and full remediation details are in `docs/SECURITY_AUDIT.md`.

**Summary (6 findings, all remediated):**

| ID | Vulnerability | Severity | Status |
|----|---------------|----------|--------|
| VULN-01 | Rate limiting absent on `/api/start` | Medium | **Fixed** — Flask-Limiter 10 req/min |
| VULN-02 | Rate limiting absent on `/api/chat` | Medium | **Fixed** — Flask-Limiter 30 req/min |
| VULN-03 | TTS endpoint lacked content policy | Medium | **Fixed** — `_TTS_BLOCKED_PATTERNS` regex filter |
| VULN-04 | `/api/start` field scrubbing incomplete | Low | **Fixed** — whitelist-based scrubbing |
| VULN-05 | Error messages leaked internal details | Low | **Fixed** — generic error strings server-side |
| VULN-06 | Input validation inconsistency | Low | **Fixed** — message cap 2,000 chars enforced |

**Post-pentest security posture:** 9/9 tests passed/blocked on re-run.

### OWASP LLM Top 10 Assessment (2025)

A second black-box pentest specifically targeting AI/LLM vulnerabilities was conducted using `backend/llm_pentest.py` (19 tests, 7 categories). Results saved to `backend/llm_security_report.json`. Full findings in `docs/SECURITY_AUDIT.md` Section 8.

**Summary (19 tests):**

| Category | Tests | Protected | Partial | Vulnerable |
|----------|-------|-----------|---------|------------|
| LLM01 — Prompt Injection | 5 | 5 | 0 | 0 |
| LLM02 — Insecure Output Handling | 2 | 1 | 1 | 0 |
| LLM04 — Model DoS | 3 | 3 | 0 | 0 |
| LLM06 — Sensitive Info Disclosure | 3 | 3 | 0 | 0 |
| LLM07 — Insecure Plugin Design | 2 | 1 | 1 | 0 |
| LLM08 — Excessive Agency | 2 | 1 | 1 | 0 |
| LLM09 — Overreliance | 2 | 1 | 0 | 1 |
| **Total** | **19** | **15** | **3** | **1** |

**Overall posture: PARTIAL** (79% protected, 1 confirmed vulnerability)

**Three LLM remediations implemented + one systemic hardening:**

| Finding | Fix | Location |
|---------|-----|----------|
| LLM09-9A: Implausible species+symptom accepted (fish barking) | `_check_plausibility()` deterministic guard + LLM rule 10 | `backend/agents/intake_agent.py` |
| LLM02-2A: User-supplied `pet_name` not HTML-encoded in summary | `_escape_pet_profile()` at output boundary | `backend/api_server.py` |
| LLM07-7B: TTS endpoint lacked content policy | `_TTS_BLOCKED_PATTERNS` regex filter before TTS API call | `backend/api_server.py` |
| LLM01 systemic: paraphrased/semantic jailbreaks not caught by regex | Stage 2 LLM semantic classifier — GPT-4o-mini screens every clean-pass message; every decision traced in LangSmith under `guardrail.llm_classifier` | `backend/guardrails.py` |

---

## STEP 7: Voice & Intake UX Hardening (March 2026)

### Voice Quality Improvements

| Dimension | Before | After |
|-----------|--------|-------|
| **TTS model** | `tts-1` (robotic, machine-like) | `tts-1-hd` (HD model, significantly more natural) |
| **TTS speed** | Default (slightly fast) | `speed=0.95` (unhurried, natural pacing) |
| **Languages covered** | 7 languages (variable quality) | All 7 languages now use `tts-1-hd` at `speed=0.95` |

### Intake UX Improvements (Free-Flowing Conversation)

| Issue | Fix |
|-------|-----|
| **Robotic rigid questioning** | `temperature` raised `0.1→0.3`; system prompt rewritten from field-collection rules to warm receptionist style |
| **Intake blocked on optional fields** | `intake_complete=True` fires as soon as species + chief_complaint both known — does **not** require timeline, eating, or energy answers |
| **Date/timeline answers rejected** | Accepts any format verbatim: "since Monday", "since March 1st", "about a week", "started yesterday" — stored as-is in `symptom_details.timeline` |
| **Re-asking answered questions** | System prompt explicitly tracks answered fields and never re-asks |

### Guardrail Classifier Default Flip

| Setting | Before | After |
|---------|--------|-------|
| `GUARDRAIL_LLM_ENABLED` | `false` (local dev default) | `true` (production default — recommended for all deployments) |
| Audit coverage | Regex only | Regex + LLM semantic classifier, every decision in LangSmith |

---

## Reference: Key Repo Documents

| Document | Purpose |
|----------|---------|
| [docs/architecture/agents.md](architecture/agents.md) | Sub-agent I/O contracts, data access policy |
| [docs/architecture/orchestrator.md](architecture/orchestrator.md) | Orchestrator responsibilities and branching |
| [docs/test_scenarios.md](test_scenarios.md) | End-to-end test scenarios and validation checklist |
| [NEXT_STEPS.md](../NEXT_STEPS.md) | Build order and due dates (Mar 22, 2026) |

---

End of Agent Design Canvas
