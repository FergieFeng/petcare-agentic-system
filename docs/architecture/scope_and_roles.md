# Scope and Roles

**Authors:** Syed Ali Turab & Fergie Feng | **Contributors:** Diana Liu | **Team:** Broadview | **Date:** March 1, 2026

This document defines the **collaboration model** for the PetCare Triage & Smart Booking Agent.
It is designed for **team-based development**, where each team member can own one or more sub-agents.

---

## Collaboration Goal

- Split the system into **independent sub-agents** with clear **input/output contracts**
- Enable teammates to work **in parallel** with minimal coordination overhead
- Integrate through a single **Orchestrator** that enforces workflow rules and safety invariants

---

## In Scope

- Designing each sub-agent's **micro-workflow**, prompt strategy, and edge cases
- Defining **input/output JSON** contracts per agent (schema-aligned)
- Implementing agent logic as:
  - **Prompt-only** (acceptable for POC), or
  - **Prompt + light code** (scoring helpers, validators, rule-based checks)
- Adding **example fixtures** for each agent (sample input + sample output)
- Orchestrator integration, safety enforcement, and schema validation
- Synthetic test data creation and evaluation
- Owner-facing chat interface (web-based)
- Clinic-facing summary output

---

## Out of Scope (POC Phase)

- Medical diagnoses or prescription advice
- Integration with real EMR/CRM/scheduling systems
- User accounts, authentication, or persistent profiles
- Multi-clinic deployment or multi-tenant architecture
- Payment processing
- Real patient data (all data is synthetic)
- SMS/email notification delivery
- Mobile app development

---

## Ownership Model

### Role: Orchestrator / Integrator (1 owner)
- Owns **execution order**, branching logic, and safety enforcement
- Manages session state across sub-agents
- Resolves conflicts between agent outputs
- Enforces canonical schema and produces:
  - Owner-facing response
  - Clinic-facing structured summary
- Owns integration tests and end-to-end demo runs

### Role: Sub-Agent Owner (1 owner per agent)
Each sub-agent owner is responsible for:
- **Micro-workflow design** (2-5 steps)
- Prompt + reasoning constraints
- Input/Output contract
- Edge cases and failure behavior
- One example fixture (input + output)

### Role: Frontend Developer (1 owner)
- Owns the chat-based intake UI
- Connects to the Flask API
- Displays owner-facing response (urgency, slots, guidance)
- Optional: clinic-facing summary view

---

## Sub-Agent Assignments

| Agent # | Agent | Owner | Deliverables (Minimum) |
|--------:|-------|-------|----------------------|
| A | Intake Agent | (assign) | Micro-workflow + I/O JSON + 1 fixture |
| B | Safety Gate Agent | (assign) | Red-flag rules + I/O JSON + 1 fixture |
| C | Confidence Gate Agent | (assign) | Validation logic + I/O JSON + 1 fixture |
| D | Triage Agent | (assign) | Urgency classification rules + I/O JSON + 1 fixture |
| E | Routing Agent | (assign) | Symptom→appointment mapping + I/O JSON + 1 fixture |
| F | Scheduling Agent | (assign) | Slot proposal logic + I/O JSON + 1 fixture |
| G | Guidance & Summary Agent | (assign) | Guidance templates + summary format + I/O JSON + 1 fixture |
| -- | Orchestrator Agent | (assign integrator) | Flow control + safety rules + E2E fixture |

> If team size is smaller, agents can be grouped (e.g., B+C together, F+G together).

---

## Definition of Done (Per Sub-Agent)

A sub-agent is considered complete when:
- It produces **schema-aligned JSON** with required keys
- It handles missing/ambiguous inputs gracefully (returns warnings or requests clarification)
- It has at least **one fixture** that can be replayed
- It does not overreach into other agents' responsibilities
- It does not provide medical diagnoses or prescriptions

---

## Working Agreement

- **Fixed schema, flexible logic:** schema remains stable; agent workflows can iterate
- **Single responsibility:** each agent does one thing well
- **Safety-first:** conservative defaults when uncertain
- **Small iterations:** changes should be testable with fixtures
- **Privacy-by-design:** no persistent PII storage
