# Agent Task Assignment

This page is the single source of truth for assigning ownership and tracking progress for the PetCare sub-agent design workstream.

## How to Use

- Assign one folder to one teammate.
- Each teammate documents prompt/workflow/contracts in their assigned folder.
- Keep outputs schema-aligned and fixture-backed.

## Team Assignment Table

| Workstream | Folder | Owner | Backup | Status | Due Date |
|-----------|--------|-------|--------|--------|----------|
| Intake Agent (A) | `docs/agent_specs/intake/` | (assign) | (assign) | Not Started | (date) |
| Safety Gate Agent (B) | `docs/agent_specs/safety_gate/` | (assign) | (assign) | Not Started | (date) |
| Confidence Gate Agent (C) | `docs/agent_specs/confidence_gate/` | (assign) | (assign) | Not Started | (date) |
| Triage Agent (D) | `docs/agent_specs/triage/` | (assign) | (assign) | Not Started | (date) |
| Routing Agent (E) | `docs/agent_specs/routing/` | (assign) | (assign) | Not Started | (date) |
| Scheduling Agent (F) | `docs/agent_specs/scheduling/` | (assign) | (assign) | Not Started | (date) |
| Guidance & Summary Agent (G) | `docs/agent_specs/guidance_summary/` | (assign) | (assign) | Not Started | (date) |
| Orchestrator Agent | `docs/agent_specs/orchestrator/` | (assign) | (assign) | Not Started | (date) |

## Required Deliverables (Per Agent Owner)

Each owner must complete all items in their assigned folder:

- `README.md` updated with owner name and scope
- `input_output_contract.md` with required and optional fields
- One strategy/rules doc (e.g., `prompt_strategy.md`, `red_flag_rules.md`, `triage_rules.md`)
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`

## Definition of Done (Per Agent)

- Output fields are compatible with `docs/architecture/output_schema.md`
- Ambiguous/missing-input behavior is documented
- At least one fixture pair can be replayed by another teammate
- No overlap with responsibilities owned by other agents
- No medical diagnoses or prescriptions in agent output

## Integration Owner Checklist (Orchestrator Owner)

- [ ] Confirm all agent contracts are mutually compatible
- [ ] Resolve schema mismatches before integration
- [ ] Document safety enforcement rules
- [ ] Document conflict-resolution rules
- [ ] Prepare one end-to-end fixture using all agent outputs
- [ ] Verify emergency escalation path works correctly
