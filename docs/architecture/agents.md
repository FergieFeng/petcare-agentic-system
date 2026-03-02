# Agents

**Author:** Syed Ali Turab | **Date:** March 1, 2026

## Agent Model

Agents are specialized sub-components that receive structured input, perform a focused task, and return structured output with evidence and confidence. The Orchestrator coordinates execution order, manages branching, and merges results.

---

## Agent Overview

| # | Agent Name | Core Responsibility | Input | Output |
|---|-----------|---------------------|-------|--------|
| A | Intake Agent | Collect pet profile + chief complaint + timeline via adaptive follow-ups | Owner free-text | Structured pet profile + symptom data |
| B | Safety Gate Agent | Detect emergency red flags and trigger escalation | Structured symptoms | Red-flag boolean + escalation message |
| C | Confidence Gate Agent | Verify required fields and overall confidence | All collected fields | Confidence score + missing fields list |
| D | Triage Agent | Assign urgency tier with rationale and confidence | Validated intake data | Urgency tier + rationale + confidence |
| E | Routing Agent | Map symptom category to appointment type / provider pool | Triage result + symptoms | Appointment type + provider pool |
| F | Scheduling Agent | Propose available slots or generate booking request | Routing result + urgency | Slot proposals / booking payload |
| G | Guidance & Summary Agent | Generate safe owner guidance + structured clinic handoff | All agent outputs | Owner guidance text + clinic JSON |
| -- | Orchestrator Agent | Coordinate workflow, manage state, enforce safety rules | All agent outputs | Final combined response |

---

## Sub-Agent Details

### A. Intake Agent

- **Trigger:** Owner initiates intake via chat
- **Logic:** Ask species, breed, age, weight, chief complaint. Then ask adaptive follow-ups based on symptom area (e.g., GI → eating/drinking/vomiting frequency; respiratory → breathing rate/cough type; injury → location/mobility/swelling)
- **Output:** `pet_profile`, `chief_complaint`, `symptom_details`, `timeline`
- **Edge Cases:** Owner provides minimal info, conflicting symptoms, exotic species

### B. Safety Gate Agent

- **Trigger:** Intake data collected
- **Logic:** Rule-based matching against known emergency red flags (breathing difficulty, uncontrolled bleeding, suspected toxin ingestion, seizures, collapse, inability to urinate)
- **Output:** `red_flag_detected` (boolean), `red_flags[]`, `escalation_message`
- **Edge Cases:** Ambiguous descriptions ("breathing funny" vs "can't breathe")

### C. Confidence Gate Agent

- **Trigger:** After safety check (if no red flag)
- **Logic:** Check required fields present, assess confidence in symptom data, detect conflicting signals
- **Output:** `confidence_score` (0-1), `missing_fields[]`, `conflicts[]`, `action` (proceed / clarify / human_review)
- **Edge Cases:** Owner contradicts themselves, critical field missing

### D. Triage Agent

- **Trigger:** Confidence gate passes
- **Logic:** Classify urgency into 4 tiers based on symptoms, timeline, and species-specific norms. Provide rationale and confidence score.
- **Output:** `urgency_tier` (Emergency / Same-day / Soon / Routine), `rationale`, `confidence`, `contributing_factors[]`
- **Edge Cases:** Borderline urgency, multiple concurrent issues

### E. Routing Agent

- **Trigger:** Triage complete
- **Logic:** Map symptom category (GI, derm, respiratory, injury/pain, dental, wellness, behavioral) to appointment type and provider pool using clinic rule map.
- **Output:** `symptom_category`, `appointment_type`, `provider_pool[]`, `special_requirements`
- **Edge Cases:** Multi-category symptoms, species requiring specialist

### F. Scheduling Agent

- **Trigger:** Routing complete
- **Logic:** Based on urgency tier and appointment type, find matching available slots from the clinic schedule. Propose top 2-3 options or generate a booking request payload.
- **Output:** `proposed_slots[]`, `booking_request` (JSON payload for clinic system)
- **Edge Cases:** No slots available for required urgency, after-hours emergency

### G. Guidance & Summary Agent

- **Trigger:** All prior agents complete
- **Logic:** Generate safe, non-diagnostic "do/don't while waiting" guidance for the owner. Produce a structured clinic-ready intake summary with all collected data.
- **Output:** `owner_guidance` (text), `clinic_summary` (structured JSON)
- **Edge Cases:** Emergency (guidance is "go to ER now"), very routine case

---

## Data Access Policy

Role-based data access enforces minimal privilege and prevents cross-responsibility leakage:

| Agent | `clinic_rules.json` | `red_flags.json` | `available_slots.json` | Intake Records | Appointments |
|-------|:-:|:-:|:-:|:-:|:-:|
| **A -- Intake** | -- | -- | -- | -- | -- |
| **B -- Safety Gate** | Read | Read | -- | -- | -- |
| **C -- Confidence Gate** | -- | -- | -- | -- | -- |
| **D -- Triage** | Read | -- | -- | -- | -- |
| **E -- Routing** | Read | -- | -- | -- | -- |
| **F -- Scheduling** | -- | -- | Read | -- | Write |
| **G -- Guidance & Summary** | -- | -- | -- | Write | -- |
| **Orchestrator** | Read | Read | Read | Read/Write | Read |

### Responsibility Boundaries

**Triage Agent (D)**
- Cannot create or modify appointments
- Cannot access scheduling data
- Operates strictly on rule-grounded logic from `clinic_rules.json`

**Scheduling Agent (F)**
- Cannot alter triage results or urgency levels
- Cannot modify clinic rules
- Only agent that writes appointment records

**Safety Gate Agent (B)**
- Cannot override urgency levels set by Triage
- Only generates escalation signals based on curated red-flag list
- Does not provide guidance text (that's Agent G's job)

**Guidance & Summary Agent (G)**
- Cannot modify triage or routing decisions
- Generates guidance using approved non-diagnostic language
- Only agent that writes intake records

This boundary enforcement reduces risk of logic entanglement and clinical inconsistency. See `docs/architecture/data_model.md` for full schema details.

---

## Common Output Contract

Each sub-agent returns:

- `agent_name` (string)
- `status` (`success` | `escalate` | `needs_review`)
- `output` (agent-specific structured data)
- `confidence` (0-1)
- `warnings[]` (if degraded or uncertain)
- `processing_time_ms` (integer)

## Agent Quality Guidelines

- Never fabricate symptoms or medical details not provided by the owner
- Never provide a diagnosis or prescribe treatment
- Use conservative defaults when uncertain (escalate rather than under-triage)
- Keep guidance language safe and non-diagnostic
- All recommendations must be actionable and specific
