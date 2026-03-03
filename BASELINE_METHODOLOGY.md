# BASELINE_METHODOLOGY — PetCare Agentic System (MMAI 891)

**Project:** PetCare Triage & Smart Booking Agentic System (Team Broadview)  
**Baseline option used:** **Option 1 only — Manual receptionist phone-call script (non-AI)**  
**Baseline purpose:** Define a clear, safety-aligned comparison point to evaluate the value of our **7-agent, safety-first architecture** against a realistic “status quo” intake workflow used by many veterinary clinics.  
**Data policy:** All scenarios are **synthetic**. No real owner/pet PHI. Session-only memory.

---

## 1) System Under Evaluation (Reference)

The full system is a monolithic **Python/Flask** app (single deployable unit) running either via Python or a single Docker container. The Orchestrator coordinates a **7-agent pipeline** per request:

- **LLM Agents:**  
  **A Intake (LLM)** → **D Triage (LLM)** → **G Guidance+Summary (LLM)**  
- **Rule Agents (local, deterministic):**  
  **B Safety Gate** → **C Confidence Gate** → **E Routing** → **F Scheduling**

Execution is sequential inside one request/response cycle (no microservices).  
Key API endpoints include:
- `POST /api/session/start`
- `POST /api/session/<id>/message`
- `GET  /api/session/<id>/summary`
- `POST /api/voice/transcribe`
- `POST /api/voice/synthesize`
- `GET  /api/health`

---

## 2) Baseline Definition (Option 1 Only)

### Baseline-1: Manual Receptionist Phone-Call Script (Non-AI)

A human receptionist follows a fixed intake script/checklist to:
- collect structured symptom information,
- decide urgency tier,
- route to a service line/provider pool,
- and propose an appointment slot using a static schedule view.

**Why this baseline is appropriate**
- It matches the real-world reference process PetCare aims to improve: high call volumes, incomplete symptom capture, inconsistent triage, and mis-booked appointments.
- It is simple, defensible, and comparable to the system using the same test scenarios and metrics.
- It remains safety-aligned (no diagnosis/prescription; conservative escalation language).

---

## 3) Baseline-1 Workflow (Manual Script)

### Step A — Intake Required Fields (Fixed Checklist)
The receptionist must capture the following (synthetic values only):
- Pet species (dog/cat), age, approximate weight
- Chief complaint (main issue)
- Symptom onset/duration (timeline)
- Severity (mild/moderate/severe)
- Key symptoms (≥ 3 relevant)
- Known conditions/medications (if provided)
- Any toxin exposure suspicion (if relevant)

**Baseline intake output:** A structured intake note (template) that mirrors the clinic-ready summary concept (does not need perfect JSON).

### Step B — Safety Check (Manual Red-Flag Review)
Receptionist performs a red-flag screen (manual judgment; no automation). If any are present, receptionist escalates immediately with conservative language:
- breathing difficulty / blue gums
- collapse/unresponsive
- seizure
- severe bleeding/major trauma
- suspected toxin ingestion with concerning signs
- uncontrolled vomiting/diarrhea with dehydration signs
- urinary blockage concerns (esp. male cats)

**Emergency handling message (baseline):**  
“This may be urgent. Please seek immediate veterinary/emergency care now.”

### Step C — Assign Urgency Tier (Manual)
Receptionist assigns one of the system’s tiers:
- **Emergency / Same-day / Soon / Routine**

### Step D — Routing (Manual Mapping Sheet)
Receptionist selects a symptom category and provider pool using a static routing table (non-automated).

### Step E — Scheduling (Manual Slot Selection)
Receptionist proposes available slots by reading from a static schedule view (derived from `backend/data/available_slots.json`).  
No optimization and no algorithmic selection—simply “next available appropriate slot.”

### Baseline Outputs (Artifacts to Record)
For each scenario, baseline produces:
1) Owner-facing response: urgency + conservative waiting guidance  
2) Clinic-facing record: structured intake note (the checklist + summary)  
3) Routing decision (service line/provider pool)  
4) Proposed appointment slot  
5) Time-to-complete intake (stopwatch)

---

## 4) Shared Test Set (Same Inputs for Fair Comparison)

All comparisons must use the **same synthetic scenarios** for both:
- Baseline-1 (manual receptionist script)
- Full PetCare agent pipeline

**Scenario source:** `docs/test_scenarios.md` (and/or an agreed expanded set)

**Minimum recommended set:** 6–10 scenarios including:
- ≥ 2 emergency/red-flag cases
- ≥ 2 routine cases
- ≥ 1 toxin/poisoning case
- ≥ 1 ambiguous case requiring clarification

### Gold Labels (Reference Answers)
For each scenario, define a team “gold label”:
- urgency tier (Emergency/Same-day/Soon/Routine)
- red-flag presence (Y/N)
- routing category/provider pool
- scheduling priority rule (immediate/today/next available)

> Note: Gold labels are team-defined (not vet-certified). Assumptions must be documented.

---

## 5) Evaluation Metrics (Aligned with README Success Metrics)

We compute the same metrics for Baseline-1 and the full system.

### M1 — Intake Completeness (Target ≥ 90%)
**Definition:** % of required fields captured from the checklist.  
`completeness = captured_required_fields / total_required_fields`

### M2 — Triage Tier Agreement (Target ≥ 80%)
Compare assigned urgency tier vs gold label.

### M3 — Routing Accuracy (Target ≥ 80%)
Compare routing decision vs expected provider pool/appointment type.

### M4 — Red-Flag Detection Rate (Target 100%)
For scenarios with red flags: was emergency escalation triggered?

### M5 — Receptionist Intake Time Reduction (Target ≥ 30%)
Compare time-to-complete intake:
- **Baseline-1:** stopwatch timing (human-run)
- **System:** user interaction + pipeline runtime (approx)
Compute % reduction relative to baseline.

### M6 — Mis-booking / Re-booking Proxy (Target ≥ 20% reduction)
Count “booking errors” where selected urgency/provider/slot violates gold label rules.

---

## 6) Voice Capability Scope for Evaluation (Non-Blocking)

Voice support exists (Tier 1 browser-native; Tier 2 Whisper+TTS; Tier 3 Realtime), but due to the short delivery window (~3 weeks) and required UI + testing effort, **voice must not be a dependency for MVP success**.

### Baseline Evaluation Rule
- Core baseline evaluation is **text-based** (English) to ensure consistent measurement.
- Voice can be demonstrated as a **stretch** and evaluated separately as usability/safety tests (not blocking MVP).

### If Voice Is Demonstrated (Separate from Baseline Metrics)
Voice safety safeguards from `TECH_STACK.md` must be followed:
- **Critical field confirmation:** duration, red-flag symptoms, species/age must be confirmed.
- **Red-flag double confirmation** before escalation; if still uncertain, escalate (conservative default).
- **Confidence-based fallback:** low-confidence STT → repeat request → suggest text → route to human if unclear.

Voice testing metrics (if tested):
- WER target: **<10%** (Whisper), **<15%** (Web Speech API)
- Critical field extraction accuracy: **≥95%**
- Emergency misclassification rate: **0%**
- Verify all 50+ red flags can be caught via voice (if included)

---

## 7) Procedure (Step-by-Step Comparison Run)

1. Freeze scenario set + gold labels.
2. Run **Baseline-1 (manual receptionist)**:
   - Teammate A reads scenario as “owner”
   - Teammate B uses the baseline checklist and records:
     - intake note
     - urgency tier
     - routing choice
     - proposed slot
     - timing
3. Run **Full PetCare system** on the same scenario text:
   - Input via `POST /api/session/<id>/message`
   - Save outputs:
     - owner-facing urgency + guidance
     - clinic-facing structured summary (JSON)
     - timing (approx)
4. Score baseline vs system using metrics M1–M6.
5. Summarize results in the report:
   - at least **one strong success case**
   - at least **one failure/edge case** + mitigation plan

---

## 8) Threats to Validity / Limitations

- Baseline depends on human consistency; receptionist skill varies.
- Scenarios are synthetic; real-world diversity may differ.
- Gold labels are team-defined; document assumptions clearly.
- The project is scaffolded/untested; early runs may surface integration defects that affect measured performance.

---

## 9) Evidence Artifacts to Save (For Report & Demo)

- This document: `docs/BASELINE_METHODOLOGY.md`
- Scenario set + gold labels (CSV/JSON)
- Baseline completed intake notes + timing logs
- System outputs: owner guidance + clinic JSON summaries
- Scoring sheet for M1–M6
- Demo screenshots/logs
- Notes on at least 1 success and 1 failure case
