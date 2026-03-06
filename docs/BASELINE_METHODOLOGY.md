# BASELINE_METHODOLOGY — PetCare Agentic System (MMAI 891)

**Author:** Diana Liu | **Team:** Broadview | **Date:** March 2026

**Project:** PetCare Triage & Smart Booking Agentic System (Team Broadview)  
**Baseline option used:** **Option 1 only — Manual receptionist phone-call script (non-AI)**  
**Baseline purpose:** Define a clear, safety-aligned comparison point to evaluate the value of our **7-agent, safety-first architecture** against a realistic "status quo" intake workflow used by many veterinary clinics.  
**Data policy:** All scenarios are **synthetic**. No real owner/pet PHI. Session-only memory.

---

## 1. System Under Evaluation (Reference)

The full system is a monolithic **Python/Flask** app (single deployable unit) running either via Python or a single Docker container. The Orchestrator coordinates a **7-agent pipeline** per request:

- **LLM Agents:**  
  **A — Intake (LLM)** → **D — Triage (LLM)** → **G — Guidance + Summary (LLM)**
- **Rule Agents (local, deterministic):**  
  **B — Safety Gate** → **C — Confidence Gate** → **E — Routing** → **F — Scheduling**

Execution is sequential inside one request/response cycle (no microservices).  
Key API endpoints:
- `POST /api/session/start`
- `POST /api/session/<id>/message`
- `GET  /api/session/<id>/summary`
- `POST /api/voice/transcribe`
- `POST /api/voice/synthesize`
- `GET  /api/health`

---

## 2. Baseline Definition

### Baseline-1: Manual Receptionist Phone-Call Script (Non-AI)

A human receptionist follows a fixed intake script/checklist to:
- collect structured symptom information,
- decide urgency tier,
- route to a service line/provider pool,
- and propose an appointment slot using a static schedule view.

**Why this baseline is appropriate:**
- It matches the real-world reference process PetCare aims to improve: high call volumes, incomplete symptom capture, inconsistent triage, and mis-booked appointments.
- It is simple, defensible, and comparable to the system using the same test scenarios and metrics.
- It remains safety-aligned (no diagnosis/prescription; conservative escalation language).

---

## 3. Baseline-1 Workflow (Manual Script)

### Step A — Intake: Fixed 10-Question Phone Script

The receptionist asks the following questions **in order**. No adaptive follow-ups are allowed beyond what is listed — this intentionally reflects the rigidity of a real manual intake call.

```
RECEPTIONIST INTAKE SCRIPT — Manual Baseline
─────────────────────────────────────────────
1.  What is your pet's name?
2.  What type of animal is it? (dog / cat / other)
3.  How old is your pet, and approximately how much does it weigh?
4.  What is the main reason for your call today?
5.  How long has this been going on?
6.  How would you describe the severity? (mild / moderate / severe)
7.  Is your pet eating and drinking normally?
8.  Has your pet vomited or had diarrhea?
9.  Is your pet in pain or showing signs of distress?
10. Has your pet been in contact with any chemicals, plants, medications,
    or human food that it shouldn't have?
─────────────────────────────────────────────
```

**Required fields checklist** (mark captured / not captured for M1):
- [ ] Species
- [ ] Age + approximate weight
- [ ] Chief complaint
- [ ] Duration of symptoms
- [ ] Severity
- [ ] Eating/drinking status
- [ ] Red flag symptoms (present or absent)
- [ ] Toxin exposure (present or absent)

**Baseline intake output:** A structured intake note using the checklist above. Does not need to be JSON — a readable template is sufficient.

---

### Step B — Safety Check (Manual Red-Flag Review)

Receptionist performs a red-flag screen based on **manual judgment** (no automation). If any of the following are present, the receptionist escalates immediately with conservative language:

- Breathing difficulty / blue gums
- Collapse / unresponsive
- Seizure
- Severe bleeding / major trauma
- Suspected toxin ingestion with concerning signs
- Uncontrolled vomiting/diarrhea with dehydration signs
- Urinary blockage concerns (especially male cats)

**Emergency handling message (baseline):**
> *"This may be urgent. Please seek immediate veterinary or emergency care now."*

---

### Step C — Assign Urgency Tier (Manual)

Receptionist assigns one of the following tiers based on their judgment:

> **Emergency / Same-day / Soon / Routine**

---

### Step D — Routing (Manual Mapping Sheet)

Receptionist selects a symptom category and provider pool using a static routing table (non-automated). Reference: same routing rules as `backend/data/clinic_rules.json`.

---

### Step E — Scheduling (Manual Slot Selection)

Receptionist proposes available slots by reading from a static schedule view derived from `backend/data/available_slots.json`. No optimization or algorithmic selection — simply "next available appropriate slot."

---

### Baseline Outputs (Artifacts to Record per Scenario)

1. Owner-facing response: urgency level + conservative waiting guidance
2. Clinic-facing record: completed intake checklist + summary note
3. Routing decision (service line / provider pool)
4. Proposed appointment slot
5. Time-to-complete intake (stopwatch, seconds)

---

## 4. Shared Test Set (Same Inputs for Fair Comparison)

All comparisons must use the **same synthetic scenarios** for both Baseline-1 and the full PetCare agent pipeline.

**Scenario source:** `docs/test_scenarios.md`

**Minimum recommended set:** 6–10 scenarios including:
- ≥ 2 emergency / red-flag cases
- ≥ 2 routine cases
- ≥ 1 toxin / poisoning case
- ≥ 1 ambiguous case requiring clarification

### Gold Labels (Define Before Testing — Do Not Change After)

For each scenario, the team must agree on a gold label **before** running any tests to avoid bias:

| Scenario | Expected Urgency Tier | Red Flag (Y/N) | Routing Category | Scheduling Priority |
|----------|-----------------------|----------------|------------------|---------------------|
| 1 — Emergency (respiratory distress, dog) | Emergency | Y | respiratory | Immediate (no booking) |
| 2 — Routine (skin itching, cat) | Soon or Routine | N | dermatological | Next available (1–3 days) |
| 3 — Toxin ingestion (chocolate, dog) | Emergency | Y | gastrointestinal | Immediate (no booking) |
| 4 — Ambiguous ("acting weird", multi-turn) | Same-day or Soon | N | other | Today / next day |
| 5 — French (vomiting cat, multilingual) | Same-day | N | gastrointestinal | Today |
| 6 — Routine (wellness visit, dog) | Routine | N | wellness | Next available |

> **Note:** Gold labels are team-defined, not vet-certified. Document all assumptions clearly in the report.

---

## 5. Evaluation Metrics (Baseline vs Agent)

Compute the same metrics for Baseline-1 and the full system on every scenario.

### Practical metrics (what to measure for both baseline and agent)

| Metric | Baseline (phone script) | Agent target |
|--------|--------------------------|--------------|
| **Time to complete intake** | e.g. 5 min (stopwatch) | e.g. 2 min (target ≥30% reduction) |
| **Required fields captured** | e.g. 70% | **>90%** |
| **Triage accuracy** | e.g. inconsistent | **>80%** (vs gold labels) |
| **Red-flag detection** | e.g. depends on staff | **100%** (zero missed emergencies) |

These align with M1–M6 below and support a clear, demo-friendly comparison.

### M1 — Intake Completeness (Target ≥ 90%)
% of required fields captured from the checklist.  
`completeness = captured_required_fields / total_required_fields (8 fields)`

### M2 — Triage Tier Agreement (Target ≥ 80%)
Compare assigned urgency tier vs gold label.

### M3 — Routing Accuracy (Target ≥ 80%)
Compare routing decision vs expected provider pool / appointment type from gold label.

### M4 — Red-Flag Detection Rate (Target 100%)
For scenarios containing red flags: was emergency escalation correctly triggered?  
**This is the most critical metric — zero missed emergencies.**

### M5 — Intake Time Reduction (Target ≥ 30%)
- Baseline-1: stopwatch timing (human-run, seconds)
- System: user interaction + pipeline runtime (approximate)
- Compute % reduction relative to baseline

### M6 — Mis-booking / Re-booking Proxy (Target ≥ 20% reduction)
Count "booking errors" where selected urgency / provider / slot violates gold label rules.

---

## 6. Results Table (Fill In During Testing)

| Scenario | Baseline Tier | Agent Tier | Match? | Baseline Time (s) | Agent Time (s) | Baseline Fields (%) | Agent Fields (%) | Red Flag Caught? |
|----------|--------------|------------|--------|-------------------|----------------|---------------------|------------------|------------------|
| 1 — Emergency (respiratory) | Emergency | Emergency | ✓ | 180 | 19.1 | 75% | N/A (emergency short-circuit) | ✓ Agent, ✓ Baseline |
| 2 — Routine (skin, cat) | Routine | Soon | ✓ | 240 | 5.9 | 87.5% | 100% | N/A (no red flag) |
| 3 — Toxin (chocolate, dog) | Emergency | Emergency | ✓ | 150 | 4.5 | 75% | N/A (emergency short-circuit) | ✓ Agent, ✓ Baseline |
| 4 — Ambiguous (multi-turn) | Soon | Soon | ✓ | 300 | 6.9 | 50% | 100% | N/A (no red flag) |
| 5 — French (vomiting cat) | Same-day | Same-day | ✓ | 270 | 7.7 | 62.5% | 100% | N/A (no red flag) |
| 6 — Routine (wellness, dog) | Routine | Routine | ✓ | 180 | 6.3 | 87.5% | 100% | N/A (no red flag) |

**Evaluation run:** March 6, 2026 | **Server:** localhost:5002 | **Full results:** `backend/evaluation_results.json`

### Summary (Baseline vs Agent)

| Metric | Baseline (Manual) | Agent | Target | Met? |
|--------|-------------------|-------|--------|------|
| **M1 — Intake Completeness** | 72.9% avg | 100% (non-emergency) | ≥ 90% | ✓ |
| **M2 — Triage Tier Agreement** | 100% (6/6) | 100% (6/6) | ≥ 80% | ✓ |
| **M4 — Red-Flag Detection** | 100% (2/2) | 100% (2/2) | 100% | ✓ |
| **M5 — Intake Time** | 220s avg (3m 40s) | 8.4s avg | ≥ 30% reduction | ✓ (96.2% reduction) |

**Baseline notes:**
- Baseline times are from simulated receptionist walkthroughs using the 10-question script (Section 3).
- Baseline field capture drops for ambiguous (Scenario 4: vague input = only 4/8 fields) and multilingual (Scenario 5: French barrier = 5/8 fields).
- Both baseline and agent correctly identified all red-flag scenarios.
- The agent's main advantage is **completeness** (adaptive follow-ups vs. fixed script) and **speed** (8.4s avg vs. 220s avg).

**One strong success:** Scenario 3 (Chocolate Toxin) — the pet "seems fine" but the Safety Gate correctly fires on "chocolate" / "dark chocolate" and short-circuits to emergency. A manual receptionist may hesitate because the owner reassures them. The agent never downgrades a red flag.

**One failure / edge case:** Scenario 4 (Ambiguous) — the Intake Agent returned invalid JSON on one turn (logged: `Intake LLM returned invalid JSON`). The orchestrator recovered via fallback, but this shows LLM output parsing is a reliability risk. Mitigation: retry with stricter prompt formatting + JSON schema enforcement.

---

## 7. Procedure (Step-by-Step Comparison Run)

1. **Freeze** scenario set and gold labels (team agreement, not changed after).
2. **Run Baseline-1** (manual receptionist):
   - Teammate A reads scenario description aloud as "pet owner"
   - Teammate B works through the 10-question script as "receptionist" and records:
     - completed intake checklist
     - urgency tier decision
     - routing choice
     - proposed slot
     - time (stopwatch)
3. **Run the full PetCare system** on the same scenario text:
   - Input via `POST /api/session/<id>/message` (text-based; voice not required for MVP).
   - Save outputs: owner-facing urgency + guidance, clinic-facing structured JSON summary, timing.
   - After pipeline completes, call `GET /api/session/<id>/summary` to obtain `evaluation_metrics`: `required_fields_captured_pct`, `red_flag_triggered`, `triage_urgency_tier`, `created_at`, `first_message_at` for scoring and time-to-complete calculation.
4. **Score** both using metrics M1–M6 and fill in the results table above.
5. **Summarize** in the report:
   - At least **one strong success case** (e.g., correct emergency escalation)
   - At least **one failure / edge case** with explanation and mitigation plan

---

## 8. Voice Capability Scope (Non-Blocking for MVP)

Voice support exists (Tier 1 browser-native; Tier 2 Whisper + TTS; Tier 3 Realtime API), but due to the short delivery window and required testing effort, **voice must not be a dependency for MVP baseline evaluation.**

- Core baseline evaluation is **text-based (English)** to ensure consistent, comparable measurement.
- Voice can be demonstrated as a **stretch feature** and evaluated separately — it does not affect M1–M6.

### If Voice Is Demonstrated (Separate from Baseline Metrics)

Voice safety safeguards from `TECH_STACK.md` must be followed:
- **Critical field confirmation:** duration, red-flag symptoms, species/age must be confirmed via voice.
- **Red-flag double confirmation** before escalation; if still uncertain, escalate (conservative default).
- **Confidence-based fallback:** low-confidence STT → repeat request → suggest text → route to human.

Voice testing metrics (if tested):

| Metric | Target |
|--------|--------|
| Word Error Rate (WER) — Whisper | < 10% |
| Word Error Rate (WER) — Web Speech API | < 15% |
| Critical field extraction accuracy | ≥ 95% |
| Emergency misclassification rate | 0% |

---

## 9. Threats to Validity / Limitations

- Baseline depends on human consistency; receptionist skill varies — document who ran each scenario.
- Scenarios are synthetic; real-world diversity may differ.
- Gold labels are team-defined; document all assumptions clearly in the report.
- The project is scaffolded but untested at time of writing; early runs may surface integration defects that affect measured performance.

---

## 10. Evidence Artifacts to Save (For Report & Demo)

- This document: `docs/BASELINE_METHODOLOGY.md`
- Scenario set + gold labels (CSV or JSON)
- Baseline completed intake notes + timing logs
- System outputs: owner guidance + clinic JSON summaries per scenario
- Scoring sheet for M1–M6 (results table above)
- Demo screenshots / logs
- Notes on at least 1 success and 1 failure case

---

*This document should be read alongside `docs/test_scenarios.md` and referenced in
`technical_report.md` under the Evaluation section.*
