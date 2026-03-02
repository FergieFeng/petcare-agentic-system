# Agent Design Specification

**Author:** Syed Ali Turab | **Date:** March 1, 2026

---

## 1. Design Objective

This document defines the detailed sub-agent architecture for the PetCare Agentic System.

The design follows strict responsibility separation, safety enforcement, and minimal cross-agent coupling.

---

## 2. Sub-Agent Responsibility Table

| # | Agent Name | Type | Primary Responsibility | Input | Output | Safety Level |
|---|-----------|------|------------------------|-------|--------|--------------|
| -- | Orchestrator | Control | Workflow order, state management, safety enforcement | Raw user input | Final response aggregation | High |
| A | Intake Agent | LLM | Structures pet info and symptom data | Raw symptom text | Structured JSON (species, age, weight, duration, symptoms) | High |
| B | Safety Gate Agent | Rules | Detects emergency red flags, triggers escalation | Structured symptoms | Red-flag boolean + escalation message | Critical |
| C | Confidence Gate Agent | Rules | Verifies required fields, scores confidence | All collected fields | Confidence score + missing fields | High |
| D | Triage Agent | LLM | Assigns urgency level based on symptoms + rules | Validated intake data | Urgency tier + rationale + confidence | Critical |
| E | Routing Agent | Rules | Maps symptom category to service line / provider | Triage result + symptoms | Appointment type + provider pool | High |
| F | Scheduling Agent | Rules | Queries availability, proposes slots | Routing + urgency | Slot proposals / booking payload | High |
| G | Guidance & Summary Agent | LLM | Generates owner guidance + clinic-facing summary | All agent outputs | Owner guidance text + clinic JSON | High |

---

## 3. Agent Invocation Flow

```
1. Orchestrator receives user input
2. Intake Agent (A) structures information
3. Safety Gate (B) checks for emergency red flags
   └── If red flag → EMERGENCY response → skip to G → END
4. Confidence Gate (C) verifies completeness
   └── If low confidence → clarify (loop to A, max 2x) or flag for receptionist
5. Triage Agent (D) assigns urgency tier
6. Routing Agent (E) classifies category + selects service line
7. Scheduling Agent (F) proposes available slots
8. Guidance & Summary Agent (G) generates outputs
9. Orchestrator assembles final response
```

---

## 4. Sub-Agent Details

### A. Intake Agent (LLM)

- **Trigger:** Owner initiates intake via chat
- **Logic:** Ask species, breed, age, weight, chief complaint. Then ask adaptive follow-ups based on symptom area (GI → eating/drinking/vomiting; respiratory → breathing rate/cough; injury → location/mobility)
- **Output:** `pet_profile`, `chief_complaint`, `symptom_details`, `timeline`
- **Edge Cases:** Minimal info, conflicting symptoms, exotic species

### B. Safety Gate Agent (Rules)

- **Trigger:** Intake data collected
- **Logic:** Rule-based matching against 50+ curated emergency red flags (breathing difficulty, uncontrolled bleeding, toxin ingestion, seizures, collapse, inability to urinate)
- **Output:** `red_flag_detected` (boolean), `red_flags[]`, `escalation_message`
- **Edge Cases:** Ambiguous descriptions ("breathing funny" vs "can't breathe")

### C. Confidence Gate Agent (Rules)

- **Trigger:** After safety check (if no red flag)
- **Logic:** Check required fields present, assess confidence in symptom data, detect conflicting signals
- **Output:** `confidence_score` (0-1), `missing_fields[]`, `conflicts[]`, `action` (proceed / clarify / human_review)
- **Edge Cases:** Owner contradicts themselves, critical field missing

### D. Triage Agent (LLM)

- **Trigger:** Confidence gate passes
- **Logic:** Classify urgency into 4 tiers based on symptoms, timeline, and species-specific norms. Provide rationale and confidence.
- **Output:** `urgency_tier` (Emergency / Same-day / Soon / Routine), `rationale`, `confidence`, `contributing_factors[]`
- **Edge Cases:** Borderline urgency, multiple concurrent issues

### E. Routing Agent (Rules)

- **Trigger:** Triage complete
- **Logic:** Map symptom category (GI, derm, respiratory, injury, dental, wellness, behavioral) to appointment type and provider pool using `clinic_rules.json`
- **Output:** `symptom_category`, `appointment_type`, `provider_pool[]`, `special_requirements`
- **Edge Cases:** Multi-category symptoms, species requiring specialist

### F. Scheduling Agent (Rules)

- **Trigger:** Routing complete
- **Logic:** Based on urgency tier and appointment type, find matching available slots from `available_slots.json`. Propose top 2-3 options.
- **Output:** `proposed_slots[]`, `booking_request` (JSON payload)
- **Edge Cases:** No slots available for required urgency, after-hours emergency

### G. Guidance & Summary Agent (LLM)

- **Trigger:** All prior agents complete
- **Logic:** Generate safe, non-diagnostic "do/don't while waiting" guidance. Produce structured clinic-ready intake summary.
- **Output:** `owner_guidance` (text), `clinic_summary` (structured JSON)
- **Edge Cases:** Emergency (guidance = "go to ER now"), very routine case

---

## 5. Data Access Policy

Role-based data access enforces minimal privilege:

| Agent | `clinic_rules` | `red_flags` | `available_slots` | Intake Records | Appointments |
|-------|:-:|:-:|:-:|:-:|:-:|
| **A — Intake** | -- | -- | -- | -- | -- |
| **B — Safety Gate** | Read | Read | -- | -- | -- |
| **C — Confidence Gate** | -- | -- | -- | -- | -- |
| **D — Triage** | Read | -- | -- | -- | -- |
| **E — Routing** | Read | -- | -- | -- | -- |
| **F — Scheduling** | -- | -- | Read | -- | Write |
| **G — Guidance & Summary** | -- | -- | -- | Write | -- |
| **Orchestrator** | Read | Read | Read | Read/Write | Read |

### Responsibility Boundaries

**Triage Agent (D)**
- Cannot create or modify appointments
- Cannot access scheduling data
- Operates strictly on rule-grounded logic

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

---

## 6. Common Output Contract

Each sub-agent returns:

- `agent_name` (string)
- `status` (`success` | `escalate` | `needs_review`)
- `output` (agent-specific structured data)
- `confidence` (0-1)
- `warnings[]` (if degraded or uncertain)
- `processing_time_ms` (integer)

---

## 7. Why Multi-Agent Instead of Single LLM Pipeline?

| Advantage | How It Helps |
|-----------|-------------|
| **Responsibility isolation** | A bug in scheduling cannot corrupt triage logic |
| **Auditability** | Every decision traceable to a specific agent with its own I/O log |
| **Independent testing** | Each agent unit-tested against its own fixtures |
| **Reduced failure cascade** | If Scheduling fails, Triage and Guidance outputs are unaffected |
| **Modular extensibility** | Adding an agent = adding one file, not rewriting the prompt |
| **Mixed execution** | Safety-critical agents are deterministic rules; only reasoning agents call the LLM |
| **Cost control** | Rule-based agents (B, C, E, F) cost nothing per request |

The architecture is a **safety-constrained orchestration system** rather than a monolithic chatbot.

---

## 8. Design Decision: 7 Agents vs. 8 Agents

The original design specified 8 agents including a separate **Category Agent** for symptom domain classification. The current implementation consolidates this into 7 agents:

| Aspect | 8-Agent Design (original) | 7-Agent Design (current) |
|--------|--------------------------|--------------------------|
| **Categorization** | Dedicated Category Agent | Handled inside Routing Agent (E) |
| **Confidence Gate** | Not present | Added as Agent C |
| **Safety Agent** | Combined detection + guidance | Split into Safety Gate (B) + Guidance (G) |

**Rationale:**
1. Categorization and routing are tightly coupled — category output is only consumed by routing
2. Confidence Gate (C) adds more value than a separate Category Agent for the POC
3. Splitting safety detection (rules) from guidance generation (LLM) improves both determinism and quality
4. Fewer agents = simpler POC to demo, test, and explain

---

## 9. Agent Quality Guidelines

- Never fabricate symptoms or medical details not provided by the owner
- Never provide a diagnosis or prescribe treatment
- Use conservative defaults when uncertain (escalate rather than under-triage)
- Keep guidance language safe and non-diagnostic
- All recommendations must be actionable and specific

---

End of Agent Design Document
