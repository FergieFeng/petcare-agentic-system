


# 🐾 Agent Design Specification

## 1. Design Objective

This document defines the detailed sub-agent architecture for the PetCare Agentic System.

The design follows strict responsibility separation, safety enforcement, and minimal cross-agent coupling.

---

## 2. Sub-Agent Responsibility Table

| Agent Name | Type | Primary Responsibility | Input | Output | Read DB | Write DB | Safety Level |
|------------|------|------------------------|--------|--------|----------|-----------|--------------|
| Orchestrator | Control Layer | Determines workflow order and agent invocation | Raw user input | Execution plan + final response aggregation | ❌ | ❌ | High |
| Intake Agent | Processing | Structures pet info and symptom data | Raw symptom description | Structured JSON (species, age, weight, duration, meds, symptoms) | ❌ | ❌ | High |
| Triage Agent | Risk Engine | Assigns urgency level based on rules | Structured intake data | Urgency level (Emergency / Same-day / Soon / Routine) | ✅ clinic_rules | ❌ | Critical |
| Category Agent | Classification | Classifies symptom domain | Structured intake data | Symptom category (GI / respiratory / skin / injury / behavior / chronic) | ❌ | ❌ | Medium |
| Routing Agent | Mapping | Maps case to correct service line or veterinarian type | Category + Urgency | Recommended service line | ✅ clinic_rules | ❌ | High |
| Booking Agent | Scheduling | Queries availability and creates appointment record | Service line + time preference | Appointment confirmation | ✅ availability_slots | ✅ appointments | High |
| Safety Agent | Guardrail | Generates waiting instructions and red-flag escalation | Category + Urgency | Conservative Do/Don't guidance | ✅ clinic_rules | ❌ | Critical |
| Summary Agent | Documentation | Generates vet-facing structured intake summary | All structured case data | Clinical summary note | ❌ | ✅ intake_records | High |

---

## 3. Agent Invocation Flow

Typical invocation order:

1. Orchestrator receives user input
2. Intake Agent structures information
3. Triage Agent determines urgency
4. Category Agent classifies symptom domain
5. Routing Agent selects service line
6. Booking Agent checks availability and confirms slot
7. Safety Agent generates waiting instructions
8. Summary Agent produces structured clinical note

The Orchestrator composes final output to the pet owner.

---

## 4. Responsibility Boundaries

### Triage Agent
- Cannot create appointments
- Cannot access scheduling data
- Operates strictly on rule-grounded logic

### Booking Agent
- Cannot alter triage results
- Cannot modify clinic rules

### Safety Agent
- Cannot override urgency level
- Only generates guidance based on approved templates

This boundary enforcement reduces risk of logic entanglement and clinical inconsistency.

---

## 5. Data Access Policy

Role-based data permissions:

- Only Booking Agent writes to `appointments`
- Only Summary Agent writes to `intake_records`
- Only rule-grounded agents read from `clinic_rules`
- No agent stores full raw conversation logs in MVP phase

This enforces minimal privilege and operational safety.

---

## 6. Why Multi-Agent Instead of Single LLM Pipeline?

Advantages of this architecture:

- Clear responsibility isolation
- Improved auditability
- Easier testing per agent
- Reduced failure cascade risk
- Modular extensibility

The architecture is designed as a safety-constrained orchestration system rather than a monolithic chatbot.

---

End of Agent Design Document