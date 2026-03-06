# Safety Gate Agent (Sub-Agent B) Spec

> **Implementation Status:** ✅ Complete — Rule-based (no LLM). 100% red-flag detection rate (M4) across all 6 test scenarios. Implemented in `backend/agents/safety_gate_agent.py`.

## Owner

- Name: Team Broadview
- Reviewer: Team Broadview

## Responsibility

Detect emergency red flags in the collected symptom data and trigger immediate escalation messaging when life-threatening conditions are identified.

## One-Line Summary

The Safety Gate Agent is a rule-based emergency detector that ensures no critical condition passes through to routine triage without proper escalation.

## Scope

- **In scope:**
  - Rule-based matching against defined emergency red flags
  - Red flags include: breathing difficulty, uncontrolled bleeding, suspected toxin ingestion, seizures, collapse, inability to urinate (cats), bloat/GDV signs, eye injuries
  - Immediate escalation messaging for detected emergencies
  - Conservative matching (flag when uncertain)

- **Out of scope:**
  - Urgency classification for non-emergency cases (handled by Triage Agent)
  - Follow-up question generation (handled by Intake Agent)
  - Medical diagnoses

## Required Deliverables

- `input_output_contract.md`
- `red_flag_rules.md`
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`
