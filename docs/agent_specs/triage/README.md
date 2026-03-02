# Triage Agent (Sub-Agent D) Spec

## Owner

- Name: (assign)
- Reviewer: (optional)

## Responsibility

Classify the urgency of the pet's condition into one of four tiers (Emergency / Same-day / Soon / Routine) based on validated symptom data, with evidence-based rationale and a confidence score.

## One-Line Summary

The Triage Agent assigns a clinically appropriate urgency tier to each intake case, enabling correct scheduling priority.

## Scope

- **In scope:**
  - Four-tier urgency classification
  - Evidence-based rationale for the assigned tier
  - Confidence scoring
  - Species-specific and symptom-area-specific triage logic
  - Handling of borderline cases (conservative defaults)

- **Out of scope:**
  - Emergency detection (already handled by Safety Gate)
  - Appointment type mapping (handled by Routing Agent)
  - Medical diagnoses or prognoses

## Required Deliverables

- `input_output_contract.md`
- `triage_rules.md`
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`
