# Triage Agent (Sub-Agent D) Spec

> **Implementation Status:** ✅ Complete — GPT-4o-mini powered. 100% triage tier agreement (M2) across all 6 test scenarios. Implemented in `backend/agents/triage_agent.py`.

## Owner

- Name: Team Broadview
- Reviewer: Team Broadview

## Responsibility

Classify the urgency of the pet's condition into one of four tiers (Emergency / Same-day / Soon / Routine) based on validated symptom data, with evidence-based rationale and a confidence score.

## One-Line Summary

The Triage Agent assigns a clinically appropriate urgency tier to each intake case, enabling correct scheduling priority.

## Inputs

In addition to species, chief complaint, timeline, eating/drinking status, and energy level, the Triage Agent now receives the full `pet_profile` dict from the Orchestrator. This includes:

- `breed` — used for breed-specific risk context
- `age` — drives the age-based urgency modifier (see below)
- `weight` — provides additional clinical context for the LLM

**Age-based urgency modifier (added 2026-03-08):** If the animal is geriatric (>8 years for dogs, >10 years for cats) or very young (<6 months), and the case is borderline between two urgency tiers, the Triage Agent bumps the classification one tier higher. This rule is encoded in the LLM system prompt.

**File changed:** `backend/agents/triage_agent.py`

## Scope

- **In scope:**
  - Four-tier urgency classification
  - Evidence-based rationale for the assigned tier
  - Confidence scoring
  - Species-specific, breed-aware, and age-aware triage logic
  - Handling of borderline cases (conservative defaults; age-based modifier)

- **Out of scope:**
  - Emergency detection (already handled by Safety Gate)
  - Appointment type mapping (handled by Routing Agent)
  - Medical diagnoses or prognoses

## Required Deliverables

- `input_output_contract.md`
- `triage_rules.md`
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`
