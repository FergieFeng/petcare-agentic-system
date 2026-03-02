# Preserved Workflow Guide (from main branch)

This file preserves the original workflow guide from the Resume Alignment Engine main branch.
It is kept for reference during the PetCare branch development.

---

## Original Context

The Resume Alignment Engine used a 7-agent architecture to evaluate job description / resume fit:

1. JD Analysis Agent
2. Resume Profiling Agent
3. Hard Match Agent
4. Hidden Signal Agent (optional)
5. Application Strategy Agent
6. Evidence Citation Agent (optional)
7. Orchestrator Agent

The PetCare project adapts this same multi-agent + orchestrator pattern for veterinary triage:

| Resume Alignment Engine | PetCare Triage Agent |
|------------------------|---------------------|
| JD Analysis Agent | Intake Agent |
| Resume Profiling Agent | Safety Gate Agent |
| Hard Match Agent | Confidence Gate Agent |
| Hidden Signal Agent | Triage Agent |
| Application Strategy Agent | Routing Agent |
| Evidence Citation Agent | Scheduling Agent |
| Orchestrator Agent | Guidance & Summary Agent + Orchestrator |

## Architectural Patterns Reused

- Multi-agent architecture with central orchestrator
- Structured JSON I/O contracts between agents
- Schema-driven output validation
- Optional agent steps with graceful degradation
- Documentation-first scaffolding approach
- Per-agent task assignment and fixture-backed testing
