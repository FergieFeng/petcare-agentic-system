# JD Analysis Agent Spec

## Owner

- Name: (assign)
- Reviewer: (optional)

## Responsibility

Parse plain-text job descriptions into structured, non-speculative requirement signals for downstream scoring and decision-making.

## One-Line Summary

The JD Analysis Agent focuses on precise, non-speculative extraction of role requirements to support downstream scoring and decision-making, while explicitly handling ambiguity and noise in real-world job descriptions.

## Scope

- In scope:
  - plain-text JD parsing (including noisy pasted LinkedIn-style text),
  - explicit signal extraction,
  - limited inferred role signals with explicit labeling.
- Out of scope:
  - links, scraping, ATS JSON, API ingestion,
  - compensation/career-growth/legal feasibility interpretation,
  - narrative recommendations or final apply/no-apply conclusions.

## Required Deliverables

- `input_output_contract.md`
- `prompt_strategy.md`
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`
