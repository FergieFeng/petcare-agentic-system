# Agent Task Assignment

This page is the single source of truth for assigning ownership and tracking progress for the PetCare sub-agent design workstream.

## How to Use

- Assign one folder to one teammate.
- Each teammate documents prompt/workflow/contracts in their assigned folder.
- Keep outputs schema-aligned and fixture-backed.

## Team Assignment Table

| Workstream | Folder | Owner | Backup | Status | Due Date |
|-----------|--------|-------|--------|--------|----------|
| Intake Agent (A) | `docs/agent_specs/intake/` | Team Broadview | Team Broadview | ✅ Done | March 6, 2026 |
| Safety Gate Agent (B) | `docs/agent_specs/safety_gate/` | Team Broadview | Team Broadview | ✅ Done | March 6, 2026 |
| Confidence Gate Agent (C) | `docs/agent_specs/confidence_gate/` | Team Broadview | Team Broadview | ✅ Done | March 6, 2026 |
| Triage Agent (D) | `docs/agent_specs/triage/` | Team Broadview | Team Broadview | ✅ Done | March 6, 2026 |
| Routing Agent (E) | `docs/agent_specs/routing/` | Team Broadview | Team Broadview | ✅ Done | March 6, 2026 |
| Scheduling Agent (F) | `docs/agent_specs/scheduling/` | Team Broadview | Team Broadview | ✅ Done | March 6, 2026 |
| Guidance & Summary Agent (G) | `docs/agent_specs/guidance_summary/` | Team Broadview | Team Broadview | ✅ Done | March 6, 2026 |
| Orchestrator Agent | `docs/agent_specs/orchestrator/` | Team Broadview | Team Broadview | ✅ Done | March 6, 2026 |

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

- [x] Confirm all agent contracts are mutually compatible
- [x] Resolve schema mismatches before integration
- [x] Document safety enforcement rules
- [x] Document conflict-resolution rules
- [x] Prepare one end-to-end fixture using all agent outputs
- [x] Verify emergency escalation path works correctly
