# JD Analysis Agent Prompt Strategy

## Objective

Extract explicit requirement signals from noisy plain-text job descriptions into structured JSON, with controlled and clearly labeled inference.

## Prompting Principles

1. Extract first, infer second.
2. Prefer explicit text spans as evidence.
3. Treat uncertainty explicitly (`ambiguous`, `unknown`, `warnings[]`).
4. Never generate narrative recommendations.
5. Output JSON only.

## Suggested Prompt Structure

### System Instruction

- You are a strict requirement extraction agent.
- Return structured JSON only.
- Extract only from provided JD text.
- If uncertain, mark ambiguity and add warnings.
- Do not fabricate requirements.

### Extraction Tasks

- Identify:
  - must-have skills,
  - nice-to-have skills,
  - responsibilities,
  - seniority signals,
  - tools/tech stack.
- Optionally identify:
  - domain,
  - location/region,
  - language requirements,
  - visa/regulatory constraints (explicit only).
- Label hard vs soft requirement phrases.
- Extract limited implicit role signals only when clearly supported by text and mark each as inferred.

### Output Requirements

- Strictly follow `input_output_contract.md`.
- Always include `warnings[]` and `notes[]` (can be empty).
- Keep arrays deduplicated and normalized (consistent casing/style).

## Decision Rules in Prompt

### Hard vs Soft

- Hard: terms such as `required`, `must`, `minimum`.
- Soft: terms such as `preferred`, `nice-to-have`, `bonus`.

### Inference Guardrails

- Allowed: implicit role expectations (ownership, ambiguity tolerance).
- Not allowed: compensation, legal feasibility, career progression assumptions.
- Never convert inferred signals into hard requirements.

### Ambiguity

- If seniority is unclear, set `seniority_level.value` to `ambiguous`.
- If conflict appears (for example `junior` and `senior` language), record warning.
- Missing field stays empty/null instead of guessed.

## Noisy JD Handling

When input includes copied page noise:

- Ignore navigation/UI artifacts and CTA text.
- Prioritize sections likely to contain requirements:
  - qualifications,
  - requirements,
  - responsibilities,
  - preferred qualifications.

## Validation Checklist Before Return

- JSON parses correctly.
- Required MVP fields exist.
- No inferred item missing `"inferred": true`.
- No hard requirement without textual basis.
- No disallowed inference categories present.
