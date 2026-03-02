# Test Scenarios & Workflow Validation

**Authors:** Syed Ali Turab & Fergie Feng | **Team:** Broadview | **Date:** March 1, 2026

---

## Purpose

This document provides concrete end-to-end test scenarios for the PetCare Triage & Smart Booking Agent. Each scenario defines the owner input, the expected behavior of every agent in the pipeline, and the expected output. These scenarios are used for:

- Implementation validation (does the pipeline produce the right result?)
- Demo preparation (realistic walkthroughs for the MMAI 891 presentation)
- Regression testing (catch regressions when agents are modified)
- Evaluation baseline (compare agent output against expected output)

---

## Scenario 1: Emergency Respiratory Distress (Dog)

### Owner Input

> "My dog is breathing fast, gums look pale, and he collapsed for a few seconds."

### Expected Agent Behavior

| Agent | Expected Action | Expected Output |
|-------|----------------|-----------------|
| **A -- Intake** | Structures key fields from free text | `species: dog`, `symptoms: [rapid_breathing, pale_gums, collapse]`, `duration: acute (minutes to hours)` |
| **B -- Safety Gate** | Matches "collapsed", "pale gums", "breathing fast" against `red_flags.json` | `red_flag_detected: true`, `red_flags: ["collapse", "pale gums", "difficulty breathing"]` |
| **Orchestrator** | Detects red flag → triggers emergency escalation path | Skips Confidence Gate, Triage, Routing, Scheduling |
| **G -- Guidance & Summary** | Generates emergency-specific output | Owner: "Seek emergency veterinary care immediately. Do not wait." Clinic: structured emergency alert JSON |

### Expected Owner-Facing Output

- Clear emergency escalation message (no diagnosis)
- Immediate routing to urgent care
- Transport guidance based on approved template
- No appointment booking (emergency = go now)

### Why This Matters

Validates that red-flag symptoms trigger rapid escalation and that safety guidance is prioritized over scheduling convenience. The Safety Gate (B) must catch all three red flags and the Orchestrator must short-circuit the pipeline.

---

## Scenario 2: Non-Urgent Skin Itching (Cat)

### Owner Input

> "My cat has been scratching her neck for a week, no bleeding, still eating normally."

### Expected Agent Behavior

| Agent | Expected Action | Expected Output |
|-------|----------------|-----------------|
| **A -- Intake** | Structures symptom data | `species: cat`, `symptoms: [scratching_neck]`, `duration: 7 days`, `appetite: normal`, `bleeding: no` |
| **B -- Safety Gate** | Checks red flags -- none matched | `red_flag_detected: false`, `red_flags: []` |
| **C -- Confidence Gate** | Checks required fields | `confidence: 0.85`, `missing_fields: []`, `action: proceed` |
| **D -- Triage** | Classifies urgency based on clinic rules | `urgency_tier: Soon` (or `Routine`), `rationale: "Chronic skin irritation, no acute danger signals"` |
| **E -- Routing** | Maps symptom category to service line | `category: dermatological`, `appointment_type: sick_visit_routine`, `providers: ["Dr. Patel", "Dr. Wilson"]` |
| **F -- Scheduling** | Finds matching available slots | `proposed_slots: [2-3 options within 1-3 days]` |
| **G -- Guidance & Summary** | Generates guidance + clinic note | Owner: "Monitor for worsening. Escalate if bleeding, swelling, or appetite loss." Clinic: structured intake JSON |

### Expected Owner-Facing Output

- Reassuring but safety-aware response
- Non-urgent appointment options (within 1-3 days)
- Clear escalation conditions if symptoms worsen
- No over-escalation (this is not an emergency)

### Why This Matters

Verifies that routine cases are not over-escalated, while still preserving conservative safety communication. The full pipeline (A → B → C → D → E → F → G) should execute without short-circuiting.

---

## Scenario 3: Toxin Ingestion -- Chocolate (Dog)

### Owner Input

> "My puppy just ate a whole bar of dark chocolate about 20 minutes ago. He seems fine right now."

### Expected Agent Behavior

| Agent | Expected Action | Expected Output |
|-------|----------------|-----------------|
| **A -- Intake** | Structures toxin event | `species: dog`, `age: puppy`, `symptoms: [chocolate_ingestion]`, `duration: 20 minutes`, `current_status: asymptomatic` |
| **B -- Safety Gate** | Matches "ate chocolate" against red flags | `red_flag_detected: true`, `red_flags: ["ate chocolate"]` |
| **Orchestrator** | Emergency escalation -- even though pet "seems fine" | Short-circuits to emergency path |
| **G -- Guidance & Summary** | Emergency guidance | Owner: "Chocolate is toxic to dogs. Seek emergency care immediately even if your puppy appears normal. Do not induce vomiting unless instructed by a vet." |

### Why This Matters

Tests the critical principle: **the pet appearing fine does NOT override a red flag**. Toxin ingestion is always an emergency regardless of current symptoms. The Safety Gate must catch this and the Orchestrator must not downgrade because of the owner's reassurance.

---

## Scenario 4: Ambiguous Symptoms with Low Confidence

### Owner Input

> "My pet is acting weird."

### Expected Agent Behavior

| Agent | Expected Action | Expected Output |
|-------|----------------|-----------------|
| **A -- Intake** | Attempts to structure -- insufficient data | `species: unknown`, `symptoms: ["acting weird"]`, `duration: unknown` |
| **B -- Safety Gate** | No clear red flags matched | `red_flag_detected: false` |
| **C -- Confidence Gate** | Required fields missing, low confidence | `confidence: 0.2`, `missing_fields: ["species", "specific_symptoms", "duration"]`, `action: clarify` |
| **Orchestrator** | Loops back to Intake for clarifying questions | Asks: "What type of pet? Can you describe what 'acting weird' looks like? How long has this been going on?" |

### Why This Matters

Tests the Confidence Gate's ability to catch incomplete intakes and the Orchestrator's clarification loop. The system should never triage or route with insufficient data. Max 2 clarification loops before routing to human receptionist.

---

## Scenario 5: Multilingual Intake (French)

### Owner Input (French)

> "Mon chat vomit depuis deux jours et ne mange plus."

### Expected Agent Behavior

| Agent | Expected Action | Expected Output |
|-------|----------------|-----------------|
| **A -- Intake** | Structures in French context, LLM responds in French | `species: chat (cat)`, `symptoms: [vomissements, inappétence]`, `duration: 2 jours` |
| **B -- Safety Gate** | Checks red flags (language-agnostic matching or LLM-assisted) | `red_flag_detected: false` (vomiting 2 days + not eating = same-day, not emergency) |
| **C -- Confidence Gate** | Verifies completeness | `confidence: 0.8`, `action: proceed` |
| **D -- Triage** | Classifies urgency | `urgency_tier: Same-day`, `rationale: "Vomiting for 2 days with appetite loss warrants same-day evaluation"` |
| **G -- Guidance & Summary** | Owner guidance in French, clinic summary in English | Owner (FR): "Surveillez votre chat. Ne lui donnez pas de nourriture pendant 12 heures..." Clinic (EN): structured JSON in English |

### Why This Matters

Validates multilingual support: the owner communicates in French, receives responses in French, but the clinic-facing summary is always in English for staff readability.

---

## Scenario 6: Voice Input with Noise (Tier 1)

### Owner Input (Spoken, partially garbled)

> STT transcript: "My dog is... [inaudible]... not eating... three days... [inaudible]..."

### Expected Behavior

| Step | Expected Action |
|------|----------------|
| **STT** | Returns partial transcript with low confidence segments |
| **Intake (A)** | Captures what it can: `species: dog`, `symptoms: [not_eating]`, `duration: 3 days` |
| **Safety Gate (B)** | No red flags in captured text |
| **Confidence Gate (C)** | Detects gaps from garbled audio | `confidence: 0.5`, `missing_fields: ["chief_complaint_detail"]`, `action: clarify` |
| **Orchestrator** | Requests clarification, suggests text fallback | "I didn't catch everything. Could you type or repeat: what other symptoms is your dog showing?" |

### Why This Matters

Validates voice safety: the system must not proceed with low-confidence voice input. It should request repetition or suggest switching to text input. Conservative behavior over silent failure.

---

## Validation Checklist

Use this checklist to verify any test run:

### Safety

- [ ] Urgency level is rule-grounded, not guessed
- [ ] No diagnosis or treatment recommendation is provided in owner response
- [ ] Red-flag symptoms always trigger emergency escalation
- [ ] Safety Gate (B) runs before any triage or routing
- [ ] Emergency path skips booking and goes straight to guidance

### Pipeline Correctness

- [ ] Routing follows category + urgency logic from `clinic_rules.json`
- [ ] Proposed slots match the urgency tier (emergency = no slots, same-day = today, etc.)
- [ ] Confidence Gate catches incomplete intakes
- [ ] Clarification loop works (max 2 rounds)

### Output Quality

- [ ] Owner-facing response is non-diagnostic and actionable
- [ ] Safety output includes explicit escalation triggers ("go to ER if...")
- [ ] Clinic summary is structured, English, and complete
- [ ] Summary output is machine-readable JSON

### Voice (if applicable)

- [ ] STT transcript confidence is checked before proceeding
- [ ] Low-confidence audio triggers clarification or text fallback
- [ ] Critical fields (species, duration, red-flag symptoms) are confirmed
- [ ] Red-flag phrases in voice input get double confirmation

### Multilingual (if applicable)

- [ ] Owner responses are in the selected language
- [ ] Clinic summary is always in English
- [ ] RTL layout applies for Arabic and Urdu
- [ ] Language code is passed to Whisper for STT accuracy

---

## Metrics

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Triage tier agreement with expected | ≥ 80% | Compare agent tier vs expected tier across all scenarios |
| Routing accuracy | ≥ 80% | Compare agent category/provider vs expected |
| Intake completeness | ≥ 90% | % of required fields captured without clarification |
| Red flag detection rate | 100% | Zero missed red flags across emergency scenarios |
| Pipeline latency (excl. interactive) | < 15s | Measure total processing time per intake |
| Voice fallback trigger rate | -- | Track how often voice → text fallback occurs |

---

End of Test Scenarios Document
