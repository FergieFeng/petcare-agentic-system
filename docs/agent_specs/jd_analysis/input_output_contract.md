# JD Analysis Agent Input/Output Contract

## Purpose

Provide structured requirement signals for downstream scoring and orchestration.
Output is JSON-only and does not include narrative conclusions.

## Input Contract

### Supported Input

```json
{
  "job_description": "string",
  "metadata": {
    "source": "optional string",
    "language": "optional string"
  }
}
```

### Input Rules

- `job_description` is required and must be plain text.
- Input may include UI noise from copied job pages.
- Links, scraping, ATS JSON, and API payloads are out of scope for this agent.

## Output Contract

### Top-Level Shape

```json
{
  "agent_name": "jd_analysis",
  "signals": {
    "must_have_skills": [],
    "nice_to_have_skills": [],
    "responsibilities": [],
    "seniority_level": {
      "value": "junior|mid|senior|lead|principal|ambiguous|unknown",
      "ambiguous": false,
      "evidence": []
    },
    "tools_tech_stack": [],
    "domain": null,
    "location_region": null,
    "language_requirements": [],
    "visa_or_regulatory_constraints": []
  },
  "implicit_signals": [],
  "hard_vs_soft_labels": {
    "hard_requirements": [],
    "soft_preferences": []
  },
  "warnings": [],
  "notes": []
}
```

### Required Output Fields (MVP)

- `signals.must_have_skills` (array of strings)
- `signals.nice_to_have_skills` (array of strings)
- `signals.responsibilities` (array of strings)
- `signals.seniority_level` (object, includes ambiguity flag)
- `signals.tools_tech_stack` (array of strings)

### Optional Output Fields (when explicitly present in JD)

- `signals.domain` (string or null)
- `signals.location_region` (string or null)
- `signals.language_requirements` (array of strings)
- `signals.visa_or_regulatory_constraints` (array of strings)

### Inference Fields

- `implicit_signals` (array of objects), allowed only for role-signal inference.
- Every inferred item must include `"inferred": true`.
- Inferred items must never be promoted into hard requirements.

Recommended shape:

```json
{
  "signal": "high ownership expectation",
  "inferred": true,
  "evidence": ["Own end-to-end delivery across teams"]
}
```

## Hard vs Soft Labeling Rules

- Hard requirement examples: `required`, `must`, `minimum`.
- Soft preference examples: `preferred`, `nice-to-have`, `bonus`.
- This agent labels hard vs soft; it does not compute final scoring weights.

Informational guidance (for downstream components):

- skills: ~40%
- experience: ~40%
- domain: ~20%

## Ambiguity Handling

When content is missing, vague, or conflicting:

- keep value as `ambiguous`, `unknown`, `null`, or empty arrays as appropriate,
- append warning strings to `warnings`,
- avoid guessing and auto-completion.

## Quality Constraints

- No hallucinated skills or requirements.
- No salary or compensation inference.
- No legal/visa feasibility assumptions beyond explicit JD text.
- No marketing/culture language converted into requirements unless explicitly stated as requirements.
