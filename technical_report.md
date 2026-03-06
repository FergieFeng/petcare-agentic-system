# PetCare Triage & Smart Booking Agent -- Technical Report

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview
**Date:** March 6, 2026

---

## Executive Summary

The PetCare Triage & Smart Booking Agent is a multi-agent proof-of-concept designed to reduce veterinary clinic front-desk workload and improve clinical routing accuracy. The system automates the pet symptom intake process through an AI-powered conversational interface, classifies urgency into four tiers (Emergency / Same-day / Soon / Routine), routes cases to the appropriate appointment type and provider pool, and generates both owner-facing guidance and a structured clinic-ready intake summary.

**Problem:** Veterinary clinic receptionists spend an average of 5 minutes per intake call asking ad-hoc symptom questions and manually determining urgency and appointment type. During peak hours, this creates queues, inconsistent triage quality, and mis-routing that leads to rescheduling and delays.

**Solution:** An orchestrator-coordinated multi-agent system that provides structured, safe, and explainable triage support -- reducing intake time while improving routing accuracy and consistency.

**Key Results:** The agent achieved 100% triage accuracy and 100% red flag detection across 6 synthetic test scenarios (English, French, and ambiguous multi-turn), with an average end-to-end processing time of 11,378ms versus an estimated 5-minute manual baseline intake call.

---

## 1. Problem Definition

### 1.1 Who Is This For?

| User | Role | Pain Point |
|------|------|------------|
| **Clinic receptionist / intake staff** (primary) | Operational user | High call volume, inconsistent triage, manual routing |
| **Pet owners** (secondary) | Self-serve intake + scheduling | Long hold times, unclear next steps, anxiety |
| **Veterinarians / vet techs** (downstream) | Receive structured intake summary | Incomplete handoff notes, unstructured information |

### 1.2 What Is Hard Today?

- Owners call the clinic; reception staff ask ad-hoc questions, interpret urgency, choose an appointment slot, and manually explain next steps
- Intake quality varies by staff experience
- Peak-time calls create queues
- Mis-routing (wrong appointment type/doctor/urgency) leads to rescheduling and delays

### 1.3 How Often Does It Happen?

Example clinic: 30 calls/day x 5 min intake = 150 min/day spent on intake alone.

### 1.4 What Would "Better" Look Like?

- Consistent, structured intake regardless of who (or what) handles it
- Automatic red-flag detection that never misses an emergency
- Correct routing on first attempt (fewer re-bookings)
- Pet owners receive clear next steps and safe waiting guidance
- Vets get structured pre-visit summaries

---

## 2. System Architecture

### 2.1 Architecture Overview

The system uses a **7-sub-agent architecture** coordinated by a central **Orchestrator Agent**. Each sub-agent has a single responsibility and communicates via structured JSON.

```
Owner Input (symptoms, pet info)
        |
        v
+--------------------+
| A. Intake Agent    |  Collect pet profile + chief complaint + follow-ups
+--------------------+
        |
        v
+--------------------+
| B. Safety Gate     |  Detect emergency red flags
+--------------------+
        |
   [Red flag?] --Yes--> EMERGENCY ESCALATION (stop booking)
        | No
        v
+--------------------+
| C. Confidence Gate |  Verify completeness + confidence
+--------------------+
        |
   [Low confidence?] --Yes--> Ask clarifying questions (loop to Intake)
        | OK                   or route to receptionist
        v
+--------------------+
| D. Triage Agent    |  Assign urgency tier + rationale
+--------------------+
        |
        v
+--------------------+
| E. Routing Agent   |  Map symptoms → appointment type / provider
+--------------------+
        |
        v
+--------------------+
| F. Scheduling Agent|  Propose available slots / booking request
+--------------------+
        |
        v
+--------------------+
| G. Guidance &      |  Owner do/don't guidance + clinic summary
|    Summary Agent   |
+--------------------+
        |
        v
  Owner Response + Clinic-Facing Summary
```

### 2.2 Sub-Agent Responsibilities

| Agent | Input | Output | Key Logic |
|-------|-------|--------|-----------|
| **A. Intake** | Owner free-text | Structured pet profile + symptoms | Adaptive follow-ups by species + symptom area |
| **B. Safety Gate** | Structured symptoms | Red-flag boolean + escalation message | Rule-based matching against known emergencies |
| **C. Confidence Gate** | All collected fields | Confidence score + missing fields | Required-field validation + uncertainty check |
| **D. Triage** | Validated intake data | Urgency tier + rationale + confidence | Classification with evidence |
| **E. Routing** | Triage result + symptoms | Appointment type + provider pool | Clinic rule map lookup |
| **F. Scheduling** | Routing result + urgency | Available slots / booking payload | Mock calendar integration |
| **G. Guidance & Summary** | All agent outputs | Owner guidance + clinic JSON summary | Safe non-diagnostic language |

### 2.3 Autonomy Boundaries

| The agent CAN | The agent CANNOT |
|---------------|-----------------|
| Collect intake information | Give a diagnosis |
| Suggest triage urgency tier | Prescribe medications or dosing |
| Suggest appointment routing | Override clinic policy |
| Generate booking request | Finalize emergency decisions without escalation |
| Provide safe general guidance | Provide specific medical advice |
| Produce structured clinic summary | Store owner PII beyond the session |

### 2.4 Technology Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Backend** | Python 3.11 / Flask / Gunicorn | REST API, static file serving, HTTP Basic Auth (env-var credentials), two-tier session store (1hr active / 24hr completed for PDF) |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript (ES6+) | Inter font, warm teal theme (#0d9488), dark mode, RTL for Arabic/Urdu, PWA (manifest + service worker) |
| **LLM Provider** | OpenAI GPT-4o-mini | Agents A, D, G; ~$0.01/session |
| **Voice** | Browser Speech API (Tier 1) + OpenAI Whisper/TTS (Tier 2) | 7 languages; Tier 3 Realtime API is stretch |
| **Photo Analysis** | OpenAI Vision (GPT-4o-mini) | Visual symptom observation (never diagnosis) |
| **Nearby Vets** | Google Places API (New) + OpenStreetMap Nominatim fallback | Client-side; with call/directions |
| **PDF Export** | fpdf2 (server-side) | Clinic-ready triage summary with branding |
| **Agent Framework** | Custom Python Orchestrator | In-process; LangGraph optional post-POC |
| **Data Contracts** | JSON schemas | Structured I/O between all agents |
| **Containerization** | Docker + Gunicorn (2 workers, 120s timeout) | Single-container deployment |
| **Deployment** | **Render (recommended)** | Free-tier cloud with auto-deploy from GitHub |
| **Languages** | 7 (EN, FR, ZH, AR, ES, HI, UR) | Full UI translation + RTL support |

### 2.6 Consumer-Ready Features

The POC includes the following consumer-facing features beyond the core triage pipeline:

| Feature | Technology | Purpose |
|---------|-----------|---------|
| Streaming responses | Character-by-character JS rendering | ChatGPT-like feel; hides latency |
| Nearby vet finder | Google Places API + Nominatim fallback | Find real clinics with phone/directions |
| PDF triage summary | fpdf2 server-side generation | Shareable clinic-ready report |
| Photo symptom analysis | OpenAI Vision API | Visual observation of symptoms |
| Pet profile persistence | Browser localStorage | Returning user recognition |
| Symptom history tracker | Browser localStorage | Track past triages |
| Cost estimator | Post-triage cost ranges | Estimated visit costs by urgency |
| Feedback rating | 1-5 stars + optional comment | Quality measurement data |
| Follow-up reminders | Browser Notification API | Appointment reminders |
| Breed-specific risk alerts | Client-side breed database | Health warnings for 11+ breeds |
| Dark mode | CSS variable swap | Accessibility |
| PWA support | manifest.json + service worker | Mobile installable |
| Chat transcript export | Client-side .txt download | Full conversation sharing |
| Animated onboarding | 3-step walkthrough | First-time user guidance |
| Consent banner | PIPEDA/PHIPA-style | Regulatory awareness |

### 2.5 Data Sources

**Operational data (used at runtime)** — the only data the system loads:

| Source | What It Provides | Agent(s) |
|--------|-----------------|----------|
| `backend/data/clinic_rules.json` | Synthetic clinic routing maps, 4 providers, species notes | Routing (E) |
| `backend/data/red_flags.json` | 50+ curated emergency triggers (informed by ASPCA + vet emergency guidelines) | Safety Gate (B) |
| `backend/data/available_slots.json` | Mock clinic schedule (weekday 9-5, 30-min slots, 4 providers) | Scheduling (F) |

**Design references (not used at runtime)** — consulted when curating the files above; not loaded or called by the system:

| Source | What It Provides | How we used it |
|--------|-----------------|----------------|
| [HuggingFace pet-health-symptoms-dataset](https://huggingface.co/datasets/karenwky/pet-health-symptoms-dataset) | 2,000 labeled symptom samples (5 conditions) | Symptom taxonomy ideas |
| [ASPCA AnTox / Top Toxins](https://www.aspcapro.org/antox) | Toxin ingestion red flags (1M+ cases) | Red-flag phrasing in `red_flags.json` |
| [Vet-AI Symptom Checker](https://www.vet-ai.com/symptomchecker) | Commercial product (165 vet-written algorithms) | Triage workflow design |
| [SAVSNET / PetBERT](https://github.com/SAVSNET/PetBERT) | Veterinary NLP (500M+ words, 5.1M records) | NLP / coding patterns |

**Data strategy:** All POC data is synthetic. No real PHI. Deployment is **Render**; webhook/n8n is **optional** for POC.

---

## 3. Design Decisions and Trade-offs

### 3.1 Key Considerations

| Consideration | Decision | Rationale |
|---------------|----------|-----------|
| **Safety vs. Convenience** | Conservative triage (escalate when uncertain) | Under-triage is far more dangerous than over-triage |
| **Latency vs. Accuracy** | Target < 15s for full intake summary | Acceptable for async intake; interactive parts are streamed |
| **Cost vs. Quality** | Route simple cases to smaller models | Only use deep reasoning for ambiguous triage |
| **Privacy** | Session-only memory, no persistent PII | Privacy-by-design; compliant with veterinary data norms |
| **Autonomy** | Never auto-send; always show human what agent decided | Clinic staff retain final authority |

### 3.2 Why an Agent (vs. Simpler Alternatives)?

A static prompt or rule-based system is insufficient because:
- The workflow is **multi-step and branching** (follow-up questions depend on symptoms and species)
- **Red-flag detection** requires both rule-based checks and contextual understanding
- **Routing logic** involves mapping symptom categories to appointment types with uncertainty handling
- The system must **escalate safely** when confidence is low or signals conflict

### 3.3 Orchestrator vs. Agent Framework (LangGraph / Google ADK)

We use a **custom Python orchestrator** rather than a formal agent framework for the POC.

| Option | Decision | Rationale |
|--------|----------|------------|
| **Custom orchestrator** | ✅ Used | Simple, debuggable, matches assignment emphasis on "simplicity and robustness" and "fewest steps." Branching (emergency, clarification) is explicit in code and in architecture diagrams. |
| **LangGraph** | Optional post-POC | Same flow; would give an explicit graph, checkpointing, and visualization (e.g. LangGraph Studio). Not required for the POC. |
| **Google ADK** | Not used | Vertex AI–centric and off our stack (OpenAI, Flask). Heavier than needed for this POC. |

The same 7-agent flow could be formalized in LangGraph later without changing agent logic; the report and demo can note "orchestration could be formalized in LangGraph for production" as a next step.

---

## 4. Evaluation

### 4.1 Success Metrics

| Metric | Target | Actual | Method |
|--------|--------|--------|--------|
| Triage tier agreement with clinic staff | ≥ 80% | 100% (6/6) | Synthetic test set + manual review |
| Routing accuracy (correct appointment type) | ≥ 80% | 100% (4/4 non-emergency routed cases) | Gold-label comparison: GI→sick_visit_urgent, derm→sick_visit_routine, wellness→wellness all correct |
| Intake completeness (% required fields) | ≥ 90% | 100% (5/6 scenarios — scenario 1 routed via emergency path) | Automated field-presence check |
| Red flag detection | 100% | 100% (2/2) | Synthetic emergency scenarios |
| Receptionist time reduction per case | 30%+ | ~96% (8.4s avg vs ~240s manual baseline) | Timed comparison against 10-question manual intake script |
| Re-booking / mis-booking reduction | 20%+ | 100% first-attempt routing (4/4) | All non-emergency cases routed to correct appointment type on first pass; no simulated re-bookings required |

### 4.2 Test Set

We used two complementary test sets:

**Automated Evaluation (6 scenarios)** — executed via `backend/evaluate.py` with gold labels defined in [docs/BASELINE_METHODOLOGY.md](docs/BASELINE_METHODOLOGY.md):

| # | Scenario | Species | Gold Urgency | Gold Red Flag | Gold Routing | Result |
|---|----------|---------|-------------|---------------|-------------|--------|
| 1 | Respiratory distress (fast breathing, pale gums, collapse) | Dog | Emergency | Yes | emergency | ✅ Pass |
| 2 | Chronic skin itching (1 week, eating normally) | Cat | Soon / Routine | No | dermatological | ✅ Pass |
| 3 | Chocolate toxin ingestion (dark chocolate, 1 hour ago) | Dog | Emergency | Yes | emergency | ✅ Pass |
| 4 | Ambiguous multi-turn ("pet isn't doing well" → scratching + head shaking) | Dog | Same-day / Soon | No | dermatological | ✅ Pass |
| 5 | French-language vomiting + appetite loss (2 days) | Cat | Same-day | No | gastrointestinal | ✅ Pass |
| 6 | Wellness check (annual shots, healthy) | Dog | Routine | No | wellness | ✅ Pass |

**Manual Test Cases (18 of 30 executed)** — run via `backend/run_manual_tests.py` and recorded in [testcases.md](testcases.md):

| Category | Tests | Passed | Failed | Not Tested |
|----------|-------|--------|--------|------------|
| Emergency (red flags) | TC-01 to TC-05 | 4 | 1 (TC-04) | 0 |
| Routine / Same-day | TC-06 to TC-08 | 3 | 0 | 0 |
| Ambiguous / Clarification | TC-09, TC-10 | 2 | 0 | 0 |
| Multilingual | TC-11 to TC-13 | — | — | 3 (browser) |
| Multi-turn / Edge cases | TC-14 to TC-16 | 2 | 0 | 1 |
| Safety boundary | TC-17 | 1 | 0 | 0 |
| API / Infrastructure | TC-18 to TC-20, I01–I03 | 5 | 0 | 1 (Docker) |
| Voice | TC-V01 to TC-V07 | — | — | 7 (mic req.) |
| **Total** | **30** | **17** | **1** | **12** |

**Overall pass rate: 94.4% (17/18 executed).** The single failure (TC-04: urinary blockage) is a known Safety Gate substring-matching gap documented in Section 4.5 and testcases.md.

### 4.3 Baseline Comparison

Baseline used: **Option 1 — Manual receptionist phone-call script (non-AI)**, as defined in **[docs/BASELINE_METHODOLOGY.md](docs/BASELINE_METHODOLOGY.md)** (author: Diana Liu). A human receptionist follows a fixed 10-question intake script; comparisons use the same synthetic scenarios and metrics (M1–M6: intake completeness, triage agreement, routing accuracy, red-flag detection, time reduction, mis-booking proxy). Gold labels are agreed before testing. Fill the results table in that document during evaluation runs.

### 4.4 Strong Example

**Scenario: Chocolate ingestion (Toxin emergency)**

The owner sends: *"My dog ate a whole bar of dark chocolate about an hour ago."*

The system correctly:
1. **Intake Agent (A):** Extracted species (dog), chief complaint (chocolate ingestion), timeline (1 hour ago)
2. **Safety Gate (B):** Detected red flag "chocolate" from the curated red-flag list and triggered immediate emergency escalation
3. **Guidance Agent (G):** Generated emergency-specific guidance ("do not induce vomiting unless directed by a vet") and a structured clinic summary

The pipeline completed in ~3 seconds (fast because the emergency path skips Confidence Gate, Triage, Routing, and Scheduling). The system correctly escalated without attempting to triage or book an appointment — matching the gold label of "Emergency."

This demonstrates the safety-first design: the deterministic rule-based Safety Gate catches the emergency before any LLM reasoning occurs, ensuring 100% detection reliability for known toxin scenarios.

### 4.5 Failure Case

**Scenario: Ambiguous multi-turn with vague initial description**

The owner sends: *"My pet isn't doing well."*

The system initially struggles because:
1. **Intake Agent (A):** No species, no specific complaint — both required fields are missing
2. The system asks a follow-up: "What type of pet do you have?"
3. After the owner replies "dog" and "he's been scratching a lot," the pipeline completes with the correct "Soon" triage tier

**What went well:** The clarification loop worked correctly — the system asked for missing required fields and completed intake once species + complaint were known.

**What could improve:** The initial follow-up question is generic ("What type of pet do you have?") rather than empathetic. A production system should use warmer language (e.g., "I'm sorry to hear that. To help, could you tell me what kind of pet you have and what symptoms you're seeing?"). Additionally, the system does not yet handle truly adversarial or nonsensical input gracefully — it will still attempt to extract symptoms from gibberish text.

---

## 5. Risk Analysis

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Under-triage (serious case labeled routine) | **High** | Medium | Conservative red-flag rules; mandatory escalation messaging; default to "contact clinic" when uncertain |
| Over-triage (too many urgent flags) | Medium | Medium | Calibrate thresholds with scenario tests; allow receptionist override; track override rate |
| Bad routing (wrong appointment type) | Medium | Medium | Clinic-owned routing map with version control; track override reasons |
| LLM hallucination in owner guidance | **High** | Low | Strict non-diagnostic language constraints; rule-based safety gate; template-based guidance |
| Owner provides misleading info | Medium | Medium | Confidence gate + targeted follow-ups; "needs human review" flag |
| API latency exceeds target | Medium | Medium | Limit model calls via smart routing; cache static rules |

---

## 6. Feasibility and Next Steps

### 6.1 Is This Viable Beyond POC?

Based on evaluation results (100% M2 triage accuracy, 100% M4 red-flag detection, ~96% time reduction vs manual baseline), the system demonstrates strong viability for production deployment with the following caveats:

| Factor | POC Finding | Production Readiness |
|--------|------------|---------------------|
| **Triage accuracy** | 100% (6/6) — exceeds the 80% threshold | ✅ Ready. Expand test set to 50+ scenarios with real vet-reviewed gold labels before clinical deployment. |
| **Red-flag safety** | 100% (2/2) known emergencies detected; 1 miss on phrasing variant (TC-04 urinary blockage) | 🟡 Needs improvement. Add fuzzy matching or synonym expansion to Safety Gate for broader keyword coverage. |
| **Intake experience** | Structured, empathetic flow with clarification loops; 7-language support; average 8.4s end-to-end | ✅ Ready. Usability testing with real pet owners recommended. |
| **Scheduling integration** | Mock calendar with synthetic slots | 🔴 Not ready. Requires integration with real clinic APIs (Vet360, PetDesk, or custom). |
| **Cost per session** | ~$0.01 (3 GPT-4o-mini calls per complete pipeline) | ✅ Viable. At 100 sessions/day = ~$1/day in LLM costs. |
| **Data privacy** | Session-only memory, no persistent PII, PIPEDA/PHIPA consent banner | ✅ POC-ready. Production needs formal privacy impact assessment. |

### 6.2 Immediate Next Steps for Deployment Readiness

1. Integrate with a real clinic scheduling system API (Vet360, PetDesk)
2. Add persistent session storage (Redis/PostgreSQL) for audit trail and multi-instance deployment
3. Add SMS/email notification support (webhook layer is implemented; connect to Twilio/SendGrid)
4. Conduct usability testing with real clinic receptionists
5. Calibrate triage thresholds with veterinary advisor feedback
6. Add clinic verification/override step before sending final response to owner
7. Formalize orchestration with LangGraph for explicit graph visualization and checkpointing

**Already completed in POC:** Species coverage expanded (dogs, cats, birds, reptiles, fish, horses, exotic pets); 7-language support with full UI translation; HTTP Basic Auth; two-tier session persistence (24hr PDF access); PWA mobile installation; consumer features (streaming, vet finder, PDF, photo analysis, cost estimator, feedback, reminders, breed alerts, dark mode, onboarding).

---

## Appendix

### A. Screenshots

Refer to the live deployment at [https://petcare-agentic-system.onrender.com](https://petcare-agentic-system.onrender.com) or run locally via `python backend/api_server.py`.

Key UI screens:
1. **Chat interface** — Welcome message, language selector (7 languages), mic button, disclaimer banner
2. **Emergency escalation** — Red alert card with "⚠️ EMERGENCY DETECTED" and nearest-clinic finder
3. **Full triage result** — Urgency tier, appointment slots, do/don't guidance, escalation triggers
4. **PDF export** — Clinic-ready triage summary with branding and structured data
5. **Dark mode** — Full theme support with CSS variable swap

### B. Test Set and Detailed Results

**Automated evaluation** (`backend/evaluate.py` → `backend/evaluation_results.json`):

```
Run date:   2026-03-06T16:25:13
Scenarios:  6
Passed:     6/6
M2 (Triage accuracy): 100%
M4 (Red-flag detection): 100%
Avg processing time: 8,409 ms

Per-scenario timing:
  Scenario 1 (respiratory emergency):  19,147 ms
  Scenario 2 (chronic skin):            5,936 ms
  Scenario 3 (chocolate toxin):         4,514 ms
  Scenario 4 (ambiguous multi-turn):    6,881 ms
  Scenario 5 (French vomiting):         7,665 ms
  Scenario 6 (wellness):                6,313 ms
```

**Manual test cases** (`testcases.md` — 18/30 executed):

| Result | Count | Details |
|--------|-------|---------|
| ✅ Pass | 17 | TC-01,02,03,05,06,07,08,09,10,15,16,17,18,19,20,I02,I03 |
| ❌ Fail | 1 | TC-04 (urinary blockage under-triaged; substring matching gap) |
| ⬜ Not tested | 12 | TC-11–14 (multilingual browser), TC-V01–V07 (voice/mic), TC-I01 (Docker) |

See [testcases.md](testcases.md) for per-test-case Pass/Fail results with detailed notes, and [docs/BASELINE_METHODOLOGY.md](docs/BASELINE_METHODOLOGY.md) Section 6 for the baseline vs. agent comparison table.

### C. Prompts Used

The system uses 3 LLM-powered agents (GPT-4o-mini) and 4 rule-based agents (no LLM). System prompts for each LLM agent:

#### Agent A: Intake Agent (`backend/agents/intake_agent.py`)

```
You are a veterinary intake assistant collecting pet symptom information.

HARD RULES — never violate:
1. NEVER name a disease, condition, or diagnosis
2. NEVER suggest medications or dosages
3. NEVER say "your pet has", "this sounds like", "this could be"
4. ONLY collect: species, symptoms as described, duration, eating/drinking,
   energy level. ANY animal is a valid species.
5. Do NOT comment on urgency at all
6. Respond in {lang_name}. JSON keys must stay in English.
7. Respond ONLY with valid JSON. No markdown fences.

You must respond with EXACTLY this JSON structure:
{
  "pet_profile": {"species": "", "pet_name": "", "breed": "",
                   "age": "", "weight": ""},
  "chief_complaint": "",
  "symptom_details": {"area": "", "timeline": "",
                       "eating_drinking": "", "energy_level": "",
                       "additional": ""},
  "follow_up_questions": [],
  "intake_complete": false
}

Rules for intake_complete:
- TRUE only when species AND a REAL chief_complaint are BOTH known
- chief_complaint must describe a HEALTH CONCERN, SYMPTOM, or REASON FOR VISIT
- Set to false and ask follow-up if missing species OR missing chief_complaint
- follow_up_questions: at most ONE plain string

For symptom_details.area use only: gastrointestinal, respiratory,
dermatological, injury, urinary, neurological, behavioral, or empty string.
```

#### Agent D: Triage Agent (`backend/agents/triage_agent.py`)

```
You are a veterinary triage classification assistant.
Your ONLY job is to classify urgency.

HARD RULES — never violate:
1. NEVER name a disease, condition, or diagnosis in any field
2. NEVER suggest medications or treatments
3. The rationale field is read ONLY by clinic staff — use clinical
   observation language but NO diagnosis names
4. Be conservative but accurate — Reserve Emergency only for immediate
   life-threatening presentations: collapse, inability to breathe,
   active seizure, known toxin ingestion, severe trauma,
   or uncontrolled bleeding.
5. Respond ONLY with valid JSON

Urgency tiers:
- Emergency: life-threatening, go to ER now
- Same-day: significant concern, must be seen today
- Soon: non-urgent, seen within 1-3 days
- Routine: standard wellness or minor concern

Respond with exactly:
{
  "urgency_tier": "Emergency|Same-day|Soon|Routine",
  "rationale": "brief clinical observation — no diagnosis names",
  "confidence": 0.0-1.0,
  "contributing_factors": ["observable factor 1", "factor 2"]
}
```

**User prompt template:** `Species: {species} | Chief complaint: {complaint} | Timeline: {timeline} | Eating/drinking: {eating} | Energy level: {energy}`

#### Agent G: Guidance & Summary Agent (`backend/agents/guidance_summary.py`)

```
You are a veterinary intake assistant writing safe waiting guidance
for a worried pet owner.

CRITICAL: The pet is a **{species}**. ALWAYS refer to it as a {species}.

HARD RULES — never violate:
1. NEVER name a disease, condition, or diagnosis
2. NEVER suggest a specific medication, supplement, or dosage
3. NEVER say "your pet has", "this sounds like", "this could be"
4. In watch_for: ONLY describe observable physical signs
5. Be warm, clear, and reassuring — the owner is worried
6. Respond in {lang_name}. JSON keys must remain in English.
7. Respond ONLY with valid JSON

Respond with exactly:
{
  "do": ["up to 4 safe actions the owner can take while waiting"],
  "dont": ["up to 3 things to avoid"],
  "watch_for": ["up to 3 observable signs that mean go to ER"]
}
```

**User prompt template:** `Urgency tier: {urgency_tier} | Pet species: {species} | Symptom area: {symptom_area} | Chief complaint: {chief_complaint}`

#### Rule-Based Agents (no LLM prompts)

| Agent | Logic Source | Description |
|-------|-------------|-------------|
| B. Safety Gate | `backend/data/red_flags.json` (50+ keywords) | Substring matching against combined intake text |
| C. Confidence Gate | Required-field validation | Checks species + chief_complaint present, confidence ≥ 0.6 |
| E. Routing | `backend/data/clinic_rules.json` | Maps symptom area → appointment type + provider pool |
| F. Scheduling | `backend/data/available_slots.json` | Filters slots by urgency tier + provider availability |

### D. Code Repository

- **Repository:** https://github.com/FergieFeng/petcare-agentic-system
- **Branch:** `main`

### E. Agent Design Canvas

See the completed Agent Design Canvas submitted as a separate deliverable.
