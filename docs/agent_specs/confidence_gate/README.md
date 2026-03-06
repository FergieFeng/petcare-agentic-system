# Confidence Gate Agent (Sub-Agent C) Spec

> **Implementation Status:** ✅ Complete — Rule-based (no LLM). Validates field completeness and triggers clarification loops. Implemented in `backend/agents/confidence_gate_agent.py`.

## Owner

- Name: Team Broadview
- Reviewer: Team Broadview

## Responsibility

Validate that all required intake fields are present, assess overall data confidence, detect conflicting signals, and determine whether to proceed, request clarification, or route to human review.

## One-Line Summary

The Confidence Gate ensures data quality and completeness before triage, catching missing info and contradictions early.

## Scope

- **In scope:**
  - Required field presence validation
  - Confidence scoring based on data completeness and coherence
  - Conflict detection (e.g., "not breathing" + "acting normal")
  - Action routing: proceed / ask clarifying questions / route to receptionist
  - Loop-back logic (max 2 clarification rounds)

- **Out of scope:**
  - Symptom interpretation or urgency classification
  - Red-flag detection (already handled by Safety Gate)
  - Medical analysis

## Required Deliverables

- `input_output_contract.md`
- `validation_rules.md`
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`
