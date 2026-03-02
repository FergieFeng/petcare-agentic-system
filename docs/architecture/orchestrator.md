# Orchestrator Agent

**Authors:** Syed Ali Turab & Fergie Feng | **Team:** Broadview | **Date:** March 1, 2026

This document describes the role and responsibilities of the **Orchestrator Agent** in the PetCare Triage & Smart Booking Agent system.

The Orchestrator is the **control and decision layer** of the system. It coordinates sub-agent execution, manages session state, enforces safety rules, and produces the final combined response.

---

## Why an Orchestrator Is Needed

The 7-sub-agent architecture defines *what* each component does, but not:

- which agents should run and in what order,
- how to handle branching (red flags → emergency escalation; low confidence → clarification loop),
- how to manage session state across agents,
- how to enforce safety invariants consistently.

Without an Orchestrator, the system would be a collection of disconnected agents rather than a coherent triage decision system.

---

## Core Responsibilities

### 1. Workflow Control

- Executes agents in the defined order: A → B → C → D → E → F → G
- Handles branching:
  - **Red flag detected** (B) → skip to emergency escalation, bypass booking
  - **Low confidence** (C) → loop back to Intake for clarifying questions or route to receptionist
  - **No slots available** (F) → generate manual booking request instead
- Supports early termination for emergencies

### 2. Session State Management

- Maintains a shared session context across all sub-agents:
  - `pet_profile`, `symptoms`, `timeline`, `red_flags`, `triage_tier`, `routing`, `booking_request`, `confidence`
- Passes only relevant data to each sub-agent
- Ensures state consistency across the intake flow

### 3. Safety Enforcement

- **Invariant:** Safety Gate (B) always runs before any triage or routing
- **Invariant:** Emergency red flags always trigger escalation messaging
- **Invariant:** Agent never provides diagnoses or prescriptions
- **Invariant:** Low-confidence cases are flagged for human review

### 4. Decision Arbitration

- Resolves conflicts between agent outputs (e.g., symptoms suggest urgency but owner says "acting normal")
- Applies conservative logic: when signals disagree, escalate rather than downgrade
- Example: High symptom severity + owner says "seems fine" → keep at higher urgency with a note

### 5. Output Assembly

- Combines all sub-agent outputs into:
  - **Owner-facing response:** urgency level, next steps, appointment options, do/don't guidance
  - **Clinic-facing summary:** structured JSON with pet profile, symptoms, triage, routing, confidence
- Validates output against the canonical schema

---

## Orchestrator Workflow

```
1. Receive owner input
2. Run Intake Agent (A) → collect structured data
3. Run Safety Gate (B) → check for red flags
   └── If red flag → EMERGENCY response → END
4. Run Confidence Gate (C) → verify completeness
   └── If low confidence → ask clarifying questions (loop to A) or flag for receptionist
5. Run Triage Agent (D) → assign urgency tier
6. Run Routing Agent (E) → determine appointment type
7. Run Scheduling Agent (F) → propose slots
8. Run Guidance & Summary Agent (G) → generate outputs
9. Assemble final response
10. Return to owner + store clinic summary
```

---

## Inputs and Outputs

### Inputs
- Owner messages (free-text)
- Session state (accumulated across turns)
- Clinic configuration (rules, schedule, red-flag list)

### Outputs
- **Owner-facing response** (natural language)
- **Clinic-facing summary** (structured JSON per `output_schema.md`)
- **Session metadata** (confidence, processing time, agent trace)

---

## Design Principles

- **Separation of concerns:** sub-agents analyze; the Orchestrator coordinates and decides.
- **Safety-first:** emergency detection always runs; conservative defaults when uncertain.
- **Deterministic branching:** workflow paths are explicit and testable.
- **Explainability:** every triage decision is traceable through the agent chain.
- **Graceful degradation:** if a sub-agent fails, the system falls back to human review rather than crashing.

---

## Scope Notes

- The Orchestrator does not perform triage or routing analysis itself.
- It does not provide diagnoses or medical advice.
- Its role is to **coordinate, enforce safety, manage state, and assemble output**.

## Implementation: Custom Orchestrator (No Framework for POC)

The Orchestrator is implemented as a **custom Python module** (`backend/orchestrator.py`), not using an agent framework such as LangGraph or Google ADK. This choice keeps the POC simple and debuggable and aligns with the assignment’s emphasis on "simplicity and robustness." The same workflow could be formalized later in **LangGraph** (explicit graph, checkpointing) without changing agent logic; **Google ADK** is not recommended (Vertex AI–centric). See PROJECT_PLAN.md Key Decisions and technical_report.md §3.3.
