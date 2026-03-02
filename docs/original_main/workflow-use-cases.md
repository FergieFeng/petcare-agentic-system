# Test Scenarios & Workflow Validation

**Authors:** Syed Ali Turab & Fergie Feng | **Team:** Broadview | **Date:** March 1, 2026

---

## Purpose

This document provides concrete end-to-end test scenarios for the PetCare Agentic System. Each scenario defines owner input, expected agent behavior, and expected output. Used for implementation validation, demo preparation, regression testing, and evaluation baselines.

---

## Scenario 1: Emergency Respiratory Distress (Dog)

### Owner Input

> "My dog is breathing fast, gums look pale, and he collapsed for a few seconds."

### Expected Agent Behavior

| Agent | Expected Action | Expected Output |
|-------|----------------|-----------------|
| **A — Intake** | Structures key fields | `species: dog`, `symptoms: [rapid_breathing, pale_gums, collapse]`, `duration: acute` |
| **B — Safety Gate** | Matches against red flags | `red_flag_detected: true`, `red_flags: ["collapse", "pale gums", "difficulty breathing"]` |
| **Orchestrator** | Emergency escalation path | Skips C, D, E, F → jumps to G |
| **G — Guidance** | Emergency-specific output | Owner: "Seek emergency care immediately." Clinic: structured emergency alert |

### Why This Matters

Validates that red-flag symptoms trigger rapid escalation and that safety guidance is prioritized over scheduling.

---

## Scenario 2: Non-Urgent Skin Itching (Cat)

### Owner Input

> "My cat has been scratching her neck for a week, no bleeding, still eating normally."

### Expected Agent Behavior

| Agent | Expected Action | Expected Output |
|-------|----------------|-----------------|
| **A — Intake** | Structures symptom data | `species: cat`, `symptoms: [scratching_neck]`, `duration: 7 days`, `appetite: normal` |
| **B — Safety Gate** | No red flags matched | `red_flag_detected: false` |
| **C — Confidence Gate** | Fields complete | `confidence: 0.85`, `action: proceed` |
| **D — Triage** | Classifies urgency | `urgency_tier: Soon`, `rationale: "Chronic skin irritation, no danger signals"` |
| **E — Routing** | Maps to dermatology | `category: dermatological`, `providers: ["Dr. Patel", "Dr. Wilson"]` |
| **F — Scheduling** | Finds slots | `proposed_slots: [2-3 within 1-3 days]` |
| **G — Guidance** | Generates guidance | Owner: "Monitor for worsening." Clinic: structured intake JSON |

### Why This Matters

Verifies routine cases are not over-escalated while preserving conservative safety communication.

---

## Scenario 3: Toxin Ingestion — Chocolate (Dog)

### Owner Input

> "My puppy just ate a whole bar of dark chocolate about 20 minutes ago. He seems fine right now."

### Expected Agent Behavior

| Agent | Expected Action | Expected Output |
|-------|----------------|-----------------|
| **A — Intake** | Structures toxin event | `species: dog`, `age: puppy`, `symptoms: [chocolate_ingestion]`, `current_status: asymptomatic` |
| **B — Safety Gate** | Matches "ate chocolate" | `red_flag_detected: true` |
| **Orchestrator** | Emergency — even though pet "seems fine" | Short-circuits to emergency path |
| **G — Guidance** | Emergency guidance | "Chocolate is toxic to dogs. Seek emergency care immediately even if appearing normal." |

### Why This Matters

Tests the principle: **"seems fine" does NOT override a red flag**. Toxin ingestion is always an emergency.

---

## Scenario 4: Ambiguous Symptoms with Low Confidence

### Owner Input

> "My pet is acting weird."

### Expected Agent Behavior

| Agent | Expected Action | Expected Output |
|-------|----------------|-----------------|
| **A — Intake** | Insufficient data | `species: unknown`, `symptoms: ["acting weird"]` |
| **B — Safety Gate** | No clear red flags | `red_flag_detected: false` |
| **C — Confidence Gate** | Required fields missing | `confidence: 0.2`, `missing_fields: ["species", "specific_symptoms", "duration"]`, `action: clarify` |
| **Orchestrator** | Clarification loop | Asks: "What type of pet? What does 'acting weird' look like? How long?" |

### Why This Matters

Tests Confidence Gate + clarification loop. System must never triage with insufficient data.

---

## Scenario 5: Multilingual Intake (French)

### Owner Input

> "Mon chat vomit depuis deux jours et ne mange plus."

### Expected Agent Behavior

| Agent | Expected Action | Expected Output |
|-------|----------------|-----------------|
| **A — Intake** | Structures in French context | `species: chat (cat)`, `symptoms: [vomiting, loss_of_appetite]`, `duration: 2 days` |
| **B — Safety Gate** | Language-agnostic matching | `red_flag_detected: false` |
| **D — Triage** | Classifies urgency | `urgency_tier: Same-day` |
| **G — Guidance** | Owner response in French, clinic summary in English | FR: "Surveillez votre chat..." EN: structured JSON |

### Why This Matters

Validates multilingual support: owner communicates in French, receives French responses, clinic summary always in English.

---

## Scenario 6: Voice Input with Noise (Tier 1)

### Owner Input (Spoken, partially garbled)

> STT transcript: "My dog is... [inaudible]... not eating... three days..."

### Expected Behavior

| Step | Expected Action |
|------|----------------|
| **STT** | Returns partial transcript with low-confidence segments |
| **Intake (A)** | Captures partial data: `species: dog`, `not_eating`, `3 days` |
| **Confidence Gate (C)** | Detects gaps | `confidence: 0.5`, `action: clarify` |
| **Orchestrator** | Requests clarification, suggests text fallback | "Could you type or repeat: what other symptoms?" |

### Why This Matters

Validates voice safety: system must not proceed with low-confidence voice input.

---

## Validation Checklist

### Safety
- [ ] Urgency level is rule-grounded, not guessed
- [ ] No diagnosis or treatment recommendation in owner response
- [ ] Red-flag symptoms always trigger emergency escalation
- [ ] Safety Gate (B) runs before any triage or routing
- [ ] Emergency path skips booking

### Pipeline Correctness
- [ ] Routing follows category + urgency logic
- [ ] Proposed slots match urgency tier
- [ ] Confidence Gate catches incomplete intakes
- [ ] Clarification loop works (max 2 rounds)

### Output Quality
- [ ] Owner response is non-diagnostic and actionable
- [ ] Safety output includes escalation triggers
- [ ] Clinic summary is structured English JSON
- [ ] Summary is machine-readable

### Voice
- [ ] STT confidence checked before proceeding
- [ ] Low-confidence → text fallback
- [ ] Critical fields confirmed via voice
- [ ] Red-flag phrases get double confirmation

### Multilingual
- [ ] Owner responses in selected language
- [ ] Clinic summary always in English
- [ ] RTL layout for Arabic and Urdu
- [ ] Language code passed to Whisper

---

## Metrics

| Metric | Target |
|--------|--------|
| Triage tier agreement | ≥ 80% |
| Routing accuracy | ≥ 80% |
| Intake completeness | ≥ 90% |
| Red flag detection rate | 100% |
| Pipeline latency | < 15s |

---

End of Test Scenarios Document
