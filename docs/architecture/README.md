# Architecture Docs Menu

Use this page as the entry point for PetCare architecture documents.

## Which File to Read

- `../AGENT_DESIGN_CANVAS.md`
  **Agent Design Canvas** (author: Diana Liu). STEP 1–5: problem definition, workflow, capabilities, data, success criteria. Includes Mermaid workflow diagram. Start here for assignment context.

- `system_overview.md`
  High-level architecture and design goals. Start here for context.

- `workflow_technical.md`
  Technical execution flow, flowchart, optional branches, and I/O examples.

- `workflow_non_technical.md`
  Plain-English workflow for non-technical readers and stakeholder communication.

- `agents.md`
  All 7 sub-agents plus orchestrator: responsibilities, I/O, and design notes.

- `orchestrator.md`
  Orchestrator responsibilities, control logic, safety enforcement, and conflict resolution.

- `output_schema.md`
  Canonical JSON output schema for both owner-facing and clinic-facing outputs.

- `scope_and_roles.md`
  Team ownership model, scope boundaries, implemented consumer features, and collaboration rules.

- `data_model.md`
  Data schemas, two-tier session store (active 1hr / completed 24hr TTL), client-side localStorage, access policy, and privacy guidance.

- `repo_structure.md`
  Repository layout including backend (Flask + auth middleware + Gunicorn), frontend (PWA, dark mode, 7 languages), and documentation structure.

## Suggested Reading Order

1. `../AGENT_DESIGN_CANVAS.md` — Agent Design Canvas (problem → workflow → success criteria)
2. `system_overview.md` — architecture, tech stack, auth, sessions, consumer features
3. `workflow_non_technical.md` (or `workflow_technical.md` for engineers)
4. `agents.md`
5. `orchestrator.md` — workflow control, two-tier sessions, Gunicorn
6. `data_model.md` — data schemas, TTL policies, localStorage
7. `output_schema.md`
8. `scope_and_roles.md` — scope, features, languages, voice tiers
9. `repo_structure.md` — directory layout
