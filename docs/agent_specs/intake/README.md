# Intake Agent (Sub-Agent A) Spec

## Owner

- Name: (assign)
- Reviewer: (optional)

## Responsibility

Collect pet profile, chief complaint, and symptom details through adaptive, multi-turn follow-up questions tailored to the species and symptom area.

## One-Line Summary

The Intake Agent conducts structured, conversational symptom collection to produce a complete pet profile and symptom record for downstream triage and routing.

## Scope

- **In scope:**
  - Multi-turn conversational intake
  - Species-specific follow-up questions (dog vs cat vs exotic)
  - Symptom-area-specific follow-ups (GI, respiratory, derm, injury, etc.)
  - Structured extraction of pet profile fields
  - Timeline and context collection

- **Out of scope:**
  - Red-flag detection (handled by Safety Gate)
  - Urgency classification (handled by Triage Agent)
  - Medical diagnoses or treatment advice
  - Owner identity collection (privacy-by-design)

## Required Deliverables

- `input_output_contract.md`
- `prompt_strategy.md`
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`
