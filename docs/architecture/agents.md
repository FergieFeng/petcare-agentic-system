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

---

## Why Multi-Agent Instead of a Single LLM Pipeline?

A single LLM prompt that takes raw owner input and produces triage + routing + scheduling + guidance in one pass is tempting but fragile. The multi-agent architecture provides:

| Advantage | How It Helps |
|-----------|-------------|
| **Responsibility isolation** | Each agent has one job. A bug in scheduling cannot corrupt triage logic. |
| **Auditability** | Every decision is traceable to a specific agent with its own input/output log. |
| **Independent testing** | Each agent can be unit-tested against its own fixtures without running the full pipeline. |
| **Reduced failure cascade** | If the Scheduling Agent fails (no slots), the Triage and Guidance outputs are unaffected. |
| **Modular extensibility** | Adding a new agent (e.g., Insurance Verification) means adding one file, not rewriting the prompt. |
| **Mixed execution modes** | Safety-critical agents (B, C) run as deterministic rules with zero cost; only reasoning-heavy agents (A, D, G) call the LLM. A single-prompt approach would force everything through the LLM. |
| **Cost control** | Rule-based agents (B, C, E, F) cost nothing per request. Only 3 of 7 agents make API calls. |

The architecture is designed as a **safety-constrained orchestration system** rather than a monolithic chatbot. The primary innovation lies in **structured triage enforcement and routing intelligence**, not conversational novelty.

---

## Design Decision: 7 Agents vs. 8 Agents (Category Agent Consolidation)

The original system design (see `docs/original_main/agent-design.md`) specified **8 sub-agents**, including a separate **Category Agent** responsible solely for classifying the symptom domain (GI, respiratory, skin, injury, behavioral, chronic).

In our implementation, we consolidated this into **7 agents** by folding symptom categorization into the **Routing Agent (E)**:

| Aspect | 8-Agent Design (original) | 7-Agent Design (current) |
|--------|--------------------------|--------------------------|
| **Categorization** | Dedicated Category Agent | Handled inside Routing Agent (E) |
| **Flow** | Intake → Safety → Triage → **Category** → Routing → Scheduling → Guidance | Intake → Safety → Confidence → Triage → **Routing** (classifies + routes) → Scheduling → Guidance |
| **Confidence Gate** | Not present | **Added** as Agent C — validates field completeness before triage |
| **Safety Agent** | Combined detection + guidance | **Split** — Safety Gate (B) detects; Guidance (G) generates text |

### Why We Made This Change

1. **Categorization and routing are tightly coupled.** The category output is only consumed by the Routing Agent. Having a separate agent pass a category string to routing adds a hop without adding value for the POC.
2. **We added a Confidence Gate instead.** The original 8-agent design lacked an explicit validation step between intake and triage. Our Confidence Gate (C) catches incomplete data and triggers clarification loops — a more impactful use of an agent slot.
3. **Safety is better as detection-only.** Splitting the original Safety Agent into a rule-based detector (B) and an LLM-powered guidance generator (G) means red-flag detection is deterministic and zero-cost, while guidance quality benefits from LLM reasoning.
4. **Fewer agents = simpler POC.** For a POC, 7 agents with clear separation is easier to demo, test, and explain than 8.

If the system moves to production, the Category Agent could be reintroduced as a standalone classifier to enable independent accuracy measurement and domain-specific tuning.
