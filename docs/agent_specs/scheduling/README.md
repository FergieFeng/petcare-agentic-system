# Scheduling Agent (Sub-Agent F) Spec

## Owner

- Name: (assign)
- Reviewer: (optional)

## Responsibility

Based on the urgency tier and appointment type, find matching available slots from the clinic schedule and propose options to the owner, or generate a booking request payload for clinic staff.

## One-Line Summary

The Scheduling Agent matches urgency and appointment type to available clinic time slots.

## Scope

- **In scope:**
  - Querying mock schedule data (`available_slots.json`)
  - Filtering by urgency tier (Emergency → same day; Routine → any available)
  - Filtering by appointment type and provider pool
  - Proposing top 2-3 slot options
  - Generating booking request payload when no direct slots available
  - Handling after-hours scenarios

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
