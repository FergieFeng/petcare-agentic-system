# Scheduling Agent (Sub-Agent F) Spec

> **Implementation Status:** ✅ Complete — Rule-based (no LLM). Matches urgency tiers to mock schedule slots. Implemented in `backend/agents/scheduling_agent.py`.

## Owner

- Name: Team Broadview
- Reviewer: Team Broadview

## Responsibility

Based on the urgency tier and appointment type, find matching available slots from the clinic schedule and propose options to the owner, or generate a booking request payload for clinic staff.

## One-Line Summary

The Scheduling Agent matches urgency and appointment type to available clinic time slots.

## Slot Generation — Fresh Per Request

**Updated:** 2026-03-08 (commit 27f39d2)

Previously, `SchedulingAgent.__init__()` called `_generate_mock_slots()` once at server startup. This meant proposed appointment dates became stale as the server ran (e.g., a server started on Monday would still propose Monday slots on Friday).

`SchedulingAgent` now stores `slots_path` at init and calls `_generate_mock_slots()` fresh inside `process()` on every request. Proposed slots are always relative to the current date and time.

**File changed:** `backend/agents/scheduling_agent.py`

## Scope

- **In scope:**
  - Querying mock schedule data (`available_slots.json`)
  - Filtering by urgency tier (Emergency → same day; Routine → any available)
  - Filtering by appointment type and provider pool
  - Proposing top 2-3 slot options
  - Generating booking request payload when no direct slots available
  - Handling after-hours scenarios
  - Slot dates always relative to current date (regenerated per request)

- **Out of scope:**
  - Real scheduling API integration (POC uses mock data)
  - Payment or insurance processing
  - Confirmation/cancellation flows
  - Triage or routing logic

## Required Deliverables

- `input_output_contract.md`
- `scheduling_logic.md`
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`
