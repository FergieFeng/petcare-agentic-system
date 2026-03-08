# Intake Agent (Sub-Agent A) Spec

> **Implementation Status:** ✅ Complete — GPT-4o-mini powered. Tested and passing across all 6 test scenarios. ~11.4s avg processing time per session. Implemented in `backend/agents/intake_agent.py`.

## Owner

- Name: Team Broadview
- Reviewer: Team Broadview

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

---

## New Method: `enrich_context(session)`

**Added:** 2026-03-08 (commit 27f39d2)

### Purpose

Replaces the rigid three-question diagnostic script (timeline → eating → energy) that previously ran after `intake_complete`. Instead of always asking the same three questions in the same order, `enrich_context()` uses GPT-4o-mini to generate ONE complaint-specific follow-up question appropriate to the current case.

### Behaviour

- Inspects already-captured context (`timeline`, `eating_drinking`, `energy_level` in session symptoms).
- If all three are already present, returns `None` (no question needed — skips immediately).
- For routine wellness visits, returns `SKIP` (no enrichment question is appropriate).
- Otherwise, calls GPT-4o-mini with the species, chief complaint, and session language (`lang_name`) to generate a single warm, contextually appropriate question.
- Increments `enrichment_count` in session state after each question.
- Capped at `MAX_ENRICHMENT_TURNS = 2` — the pipeline always advances to Safety Gate after two enrichment turns regardless of what context has been collected.

### Examples

| Complaint | Question generated |
|-----------|--------------------|
| Dog limping | "When did you first notice the limping?" |
| Cat vomiting | "Is she still keeping water down?" |
| Routine checkup | SKIP (no question asked) |

### Signature

```
enrich_context(session) -> str | None
```

- **Decorator:** `@traceable(name="intake.enrich_context", tags=["intake", "enrichment"])` (LangSmith tracing)
- **Model:** GPT-4o-mini
- **Max tokens:** 80
- **Temperature:** 0.4
- **Returns:** Plain question string, `None` (no question needed), or `None` when capped.
- **LLM call:** Goes through `llm_call_with_retry()` from `backend/utils/llm_utils.py` (exponential backoff).

### Files changed

- `backend/agents/intake_agent.py` — new `enrich_context()` method
- `backend/orchestrator.py` — replaced ~35 lines of fixed diagnostic loop with ~12 lines calling `enrich_context()`
