# Routing Agent (Sub-Agent E) Spec

> **Implementation Status:** ✅ Complete — Rule-based (no LLM). Maps symptom categories to appointment types and provider pools. Implemented in `backend/agents/routing_agent.py`.

## Owner

- Name: Team Broadview
- Reviewer: Team Broadview

## Responsibility

Classify the symptom category and map it to the appropriate appointment type and provider pool using the clinic's routing rules.

## One-Line Summary

The Routing Agent translates triage results and symptom data into a concrete appointment type and provider assignment.

## Scope

- **In scope:**
  - Symptom category classification (GI, derm, respiratory, injury/pain, dental, wellness, behavioral, etc.)
  - Mapping to appointment type (emergency, sick_visit_urgent, sick_visit_routine, wellness, specialist_referral)
  - Provider pool selection based on category and availability
  - Special requirements notation (e.g., imaging, surgery prep)
  - Species-specific routing (e.g., exotic → specialist)

- **Out of scope:**
  - Urgency classification (handled by Triage Agent)
  - Slot availability checking (handled by Scheduling Agent)
  - Medical diagnoses

## Required Deliverables

- `input_output_contract.md`
- `routing_rules.md`
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`
