# Guidance & Summary Agent (Sub-Agent G) Spec

> **Implementation Status:** ✅ Complete — GPT-4o-mini powered. Generates safe, non-diagnostic owner guidance and structured clinic summaries. Implemented in `backend/agents/guidance_summary_agent.py`.

## Owner

- Name: Team Broadview
- Reviewer: Team Broadview

## Responsibility

Generate safe, non-diagnostic "do/don't while waiting" guidance for the pet owner and produce a structured, clinic-ready intake summary containing all collected data.

## One-Line Summary

The Guidance & Summary Agent creates both the owner-facing waiting guidance and the clinic-facing structured handoff note.

## Scope

- **In scope:**
  - Owner-facing "do" list (safe actions while waiting)
  - Owner-facing "don't" list (actions to avoid)
  - Owner-facing "watch for" list (escalation cues — when to go to ER)
  - Clinic-facing structured JSON summary (per `output_schema.md`)
  - Language must be safe, non-diagnostic, and non-prescriptive

- **Out of scope:**
  - Diagnoses or treatment plans
  - Medication recommendations
  - Follow-up care instructions (that's the vet's job)
  - Triage or routing decisions

## Required Deliverables

- `input_output_contract.md`
- `guidance_templates.md`
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`
