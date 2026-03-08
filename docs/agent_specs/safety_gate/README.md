# Safety Gate Agent (Sub-Agent B) Spec

> **Implementation Status:** ✅ Complete — Rule-based (no LLM). 100% red-flag detection rate (M4) across all 6 test scenarios. Implemented in `backend/agents/safety_gate_agent.py`.

## Owner

- Name: Team Broadview
- Reviewer: Team Broadview

## Responsibility

Detect emergency red flags in the collected symptom data and trigger immediate escalation messaging when life-threatening conditions are identified.

## One-Line Summary

The Safety Gate Agent is a rule-based emergency detector that ensures no critical condition passes through to routine triage without proper escalation.

## Scope

- **In scope:**
  - Rule-based matching against defined emergency red flags
  - Red flags include: breathing difficulty, uncontrolled bleeding, suspected toxin ingestion, seizures, collapse, inability to urinate (cats), bloat/GDV signs, eye injuries
  - Immediate escalation messaging for detected emergencies
  - Conservative matching (flag when uncertain)

- **Out of scope:**
  - Urgency classification for non-emergency cases (handled by Triage Agent)
  - Follow-up question generation (handled by Intake Agent)
  - Medical diagnoses

- **Complementary system:**
  - The **comprehensive content-safety guardrails** (`backend/guardrails.py`) run **before** the Safety Gate in the pipeline. They screen for adversarial / toxic / off-topic input (8 categories: prompt injection, data extraction, violence/weapons, sexual/explicit, human-as-pet, substance abuse, abuse/harassment, trolling) with multilingual support and leet-speak normalization. The Safety Gate focuses on **medical emergency detection** from legitimate pet health concerns.

## Required Deliverables

- `input_output_contract.md`
- `red_flag_rules.md`
- `fixtures/sample_input.json`
- `fixtures/sample_output.json`

---

## Temporal Past-Incident Filter (`_is_past_incident`)

**Added:** 2026-03-08 (commit 27f39d2)

### Problem

Before this change, the Safety Gate's substring matching fired on all mentions of red-flag keywords, including past-incident descriptions. For example:

- "my dog ate chocolate **last year**" → incorrectly triggered EMERGENCY escalation
- "she had a seizure **before**, but now she just has a limp" → incorrectly triggered EMERGENCY escalation

### Solution

New helper function `_is_past_incident(text, flag)` runs after each flag match is found:

1. Locates the match position in the input text.
2. Extracts a ±80-character window around the match.
3. Checks the window for temporal past markers in all 7 supported languages.
4. If a past-tense marker is found near the flag, the flag is **skipped** (not escalated).

### Temporal markers by language

| Language | Example markers |
|----------|----------------|
| English (EN) | last year, ago, previously, used to, last week, before, back then |
| French (FR) | l'année dernière, avant, auparavant, il y a |
| Spanish (ES) | el año pasado, hace, anteriormente, antes |
| Chinese (ZH) | 去年, 以前, 曾经, 之前 |
| Arabic (AR) | العام الماضي, سابقاً, في الماضي, قبل |
| Hindi (HI) | पिछले साल, पहले, पूर्व में |
| Urdu (UR) | گزشتہ سال, پہلے, سابق |

### Behaviour

- Current incidents are unaffected — "my dog is having a seizure right now" still triggers EMERGENCY.
- Only past-tense context within ±80 characters of the flag match causes the skip.
- Conservative: if no temporal marker is found, the flag is treated as current and escalation proceeds normally.

**File changed:** `backend/agents/safety_gate_agent.py`
