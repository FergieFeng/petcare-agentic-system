# Real Use Case Workflows

Date: 2026-02-28

## Purpose

This document provides practical end-to-end examples of how the PetCare Agentic System should behave in real clinic scenarios.

It is intended for handoff, implementation alignment, and quick validation of expected agent behavior.

## Use Case 1: Emergency Respiratory Distress (Dog)

### Scenario

A pet owner reports:

> "My dog is breathing fast, gums look pale, and he collapsed for a few seconds."

### Expected workflow

1. **Orchestrator** receives free-text symptom report.
2. **Intake Agent** structures key fields:
   - species: dog
   - symptom duration: acute (minutes to hours)
   - red-flag signals: breathing difficulty, collapse, pale gums
3. **Triage Agent** applies `clinic_rules` and sets urgency to **Emergency**.
4. **Category Agent** classifies case as **respiratory / critical**.
5. **Routing Agent** maps case to **urgent/emergency service line**.
6. **Booking Agent** checks nearest immediate availability (or emergency intake path).
7. **Safety Agent** returns conservative immediate instructions:
   - seek emergency care now
   - avoid waiting at home
   - transport guidance based on approved template
8. **Summary Agent** writes structured handoff note for clinical staff.

### Expected owner-facing outcome

- Clear emergency escalation message (no diagnosis).
- Immediate routing to urgent care workflow.
- Appointment/intake confirmation if slot system supports emergency flow.

### Why this matters

This validates that red-flag symptoms trigger rapid escalation and that safety guidance is prioritized over scheduling convenience.

---

## Use Case 2: Non-Urgent Skin Itching (Cat)

### Scenario

A pet owner reports:

> "My cat has been scratching her neck for a week, no bleeding, still eating normally."

### Expected workflow

1. **Orchestrator** captures initial concern.
2. **Intake Agent** structures:
   - species: cat
   - duration: 7 days
   - behavior/appetite: normal
   - no emergency red flags reported
3. **Triage Agent** classifies urgency as **Soon** or **Routine** based on clinic rules.
4. **Category Agent** classifies symptom domain as **skin**.
5. **Routing Agent** maps to **general practice or dermatology**.
6. **Booking Agent** offers next suitable non-emergency slots.
7. **Safety Agent** provides approved waiting guidance:
   - monitor for worsening signs
   - escalation triggers (bleeding, swelling, appetite drop, lethargy)
8. **Summary Agent** stores structured intake record for vet review.

### Expected owner-facing outcome

- Reassuring but safety-aware response.
- Correct non-urgent appointment options.
- Clear escalation conditions if symptoms worsen.

### Why this matters

This verifies that routine cases are not over-escalated, while still preserving conservative safety communication.

---

## Quick validation checklist

- Urgency level is rule-grounded, not guessed.
- No diagnosis is provided in owner response.
- Routing follows category + urgency logic.
- Safety output includes explicit escalation triggers.
- Summary output is structured and clinic-readable.

