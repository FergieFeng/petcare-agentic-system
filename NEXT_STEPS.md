# Next Steps to Build the PetCare POC

**Authors:** Syed Ali Turab & Fergie Feng | **Team:** Broadview | **Date:** March 1, 2026

**Due date:** March 22, 2026 · **Target build complete:** March 10–11, 2026 · *Last updated: March 2, 2026*

This document is the **action plan** to go from “scaffolded, untested” to a **working, demo-ready POC**. Follow in order. Update the README “Next steps” table as you complete each item.

---

## Current State (as of March 2026)

| Component | Status | Blocker / Note |
|-----------|--------|-----------------|
| **API server** | Stub | Does not call Orchestrator; returns placeholder text |
| **Orchestrator** | Implemented | Imports all 7 agents; flow and branching logic in place |
| **Intake Agent (A)** | Stub | Always returns `intake_complete: False` → pipeline never proceeds past first reply |
| **Safety Gate (B)** | Implemented | Rule-based; reads `red_flags.json` |
| **Confidence Gate (C)** | Implemented | Rule-based; REQUIRED_FIELDS, action thresholds |
| **Triage (D)** | Implemented | Rule-based heuristic (HIGH_URGENCY_SIGNALS, etc.) |
| **Routing (E)** | Implemented | Reads `clinic_rules.json` |
| **Scheduling (F)** | Implemented | Reads `available_slots.json` |
| **Guidance & Summary (G)** | Implemented | Template-based owner guidance + clinic summary |
| **Frontend** | Implemented | Chat UI, language selector, voice controls; calls API |
| **Data files** | Present | `red_flags.json`, `clinic_rules.json`, `available_slots.json` |

**Main gap:** The API never invokes the Orchestrator, and the Intake agent never marks intake complete, so the full pipeline never runs end-to-end.

---

## Phase A: Get One End-to-End Request Working (1–2 days)

### Step 1: Wire the Orchestrator into the API

**File:** `backend/api_server.py`

In `handle_message()`, replace the TODO block (lines ~268–299) with a call to the Orchestrator:

1. Import the Orchestrator and ensure the session dict has the shape the Orchestrator expects (`pet_profile`, `symptoms`, `agent_outputs`, `clarification_count`, etc.).
2. Call `orchestrator = Orchestrator(session, config={})` then `result = orchestrator.process(user_message)`.
3. Return `result['message']` (and optional `state`, `emergency`, `metadata`) to the client.
4. Update `session['state']`, `session['agent_outputs']`, and `session['messages']` from the orchestrator result so the next message has correct context.

**Success:** Sending any message returns a response from the pipeline (even if the text is “I need more information” from the Intake stub).

### Step 2: Allow the Pipeline to Proceed Past Intake (unblock flow)

The Intake agent currently always returns `intake_complete: False`, so the Orchestrator always exits after Intake with a follow-up. You need at least one of:

**Option A — Quick demo (no LLM):** In `backend/agents/intake_agent.py`, add a simple rule: e.g. if `user_message` contains “dog” or “cat” and has more than 10 words, set `intake_complete: True` and fill `pet_profile` / `chief_complaint` / `symptom_details` from simple keyword parsing. That lets you run the full pipeline (Safety → Confidence → Triage → Routing → Scheduling → Guidance) for testing.

**Option B — LLM-powered (recommended for real use):** Implement the TODO in the Intake agent:

- Call OpenAI or Anthropic with a system prompt that: extracts species, chief complaint, timeline, and symptom details; never diagnoses; responds in the session language.
- From the LLM response, populate `pet_profile`, `chief_complaint`, `symptom_details` and set `intake_complete: True` when required fields (e.g. species + chief_complaint) are present; otherwise return `follow_up_questions`.
- Pass `session['language']` into the prompt so the assistant and follow-up questions use the correct language.

**Success:** For a message like “My dog has been vomiting for 2 days and isn’t eating,” the pipeline runs A → B → C → D → E → F → G and returns triage + guidance + (if implemented) slot options.

### Step 3: Smoke Test Locally

1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY` (and optionally `ANTHROPIC_API_KEY` if you use Claude).
2. From repo root:  
   `cd backend && pip install -r ../requirements.txt && python api_server.py`
3. Open `http://localhost:5002` in a browser.
4. Start a session, send: “My dog has been vomiting for 2 days.”
5. Confirm you get a non-stub response (triage tier, guidance, and no 500 errors).

**Success:** One full request flows through the entire pipeline and returns an owner-facing message.

---

## Phase B: Validate Against Test Scenarios (2–3 days)

Use the scenarios in **`docs/test_scenarios.md`** to verify behavior.

### Priority order

1. **Scenario 1 (Emergency respiratory distress)**  
   Input: *“My dog is breathing fast, gums look pale, and he collapsed for a few seconds.”*  
   - Safety Gate must set `red_flag_detected: true`.  
   - Orchestrator must short-circuit to emergency path (no triage/routing/booking).  
   - Owner sees clear “seek emergency care” message.

2. **Scenario 3 (Toxin — chocolate)**  
   Input: *“My puppy just ate a whole bar of dark chocolate about 20 minutes ago. He seems fine right now.”*  
   - Safety Gate must flag “ate chocolate.”  
   - Emergency path again; no downgrade because the pet “seems fine.”

3. **Scenario 2 (Non-urgent skin)**  
   Input: *“My cat has been scratching her neck for a week, no bleeding, still eating normally.”*  
   - Full pipeline A → G.  
   - No red flags; triage = Soon or Routine; routing = dermatological; proposed slots.

4. **Scenario 4 (Ambiguous / low confidence)**  
   Input: *“My pet is acting weird.”*  
   - Confidence Gate should set `action: clarify` and list missing fields.  
   - Orchestrator should ask for clarification (species, specific symptoms, duration); after max 2 loops, route to human review.

Fix any agent or orchestrator behavior that doesn’t match the expected tables in `docs/test_scenarios.md`. Use the **Validation Checklist** at the end of that doc for safety, pipeline correctness, and output quality.

---

## Phase C: Harden and Add Optional Features (1–2 weeks)

Once Scenarios 1–4 pass:

| Task | Where | Effort |
|------|--------|--------|
| **Intake LLM** (if you used Option A) | `backend/agents/intake_agent.py` | 1–2 days |
| **Language in prompts** | Pass `session['language']` into Intake, Triage, Guidance; add “Respond in [language]” to system prompts | ~0.5 day |
| **Voice Tier 1** | Frontend already has mic/TTS hooks; verify Web Speech API and `/api/voice/transcribe`, `/api/voice/synthesize` | ~0.5 day |
| **Voice Tier 2** | Confirm Whisper + TTS endpoints with real audio; add language hint to transcribe | ~0.5 day |
| **n8n** | Run n8n (Docker or cloud); add webhook POST from `api_server.py` when intake completes or red flag detected; build Emergency Alert + Clinic Summary workflows | 1–2 days |
| **Error handling** | Try/except in Orchestrator and API; timeouts for LLM calls; friendly error messages in UI | ~0.5 day |
| **Docker** | `docker build` / `docker-compose up`; run smoke test in container | ~0.5 day |

---

## Phase D: Evaluation and Deliverables (per PROJECT_PLAN.md)

- **Due date:** March 22, 2026. **Target build complete:** March 10–11, 2026.
- **Phase 5:** Build a test set of 20+ scenarios (reuse/expand `docs/test_scenarios.md`). Measure triage agreement, routing accuracy, intake completeness, red-flag detection. Document one strong example and one failure with learnings.
- **Phase 6:** Technical report (`technical_report.md`), 10–15 min demo video (problem, live demo, results), **deploy to Render** (recommended), README polish.

---

## Quick Reference: Key Files

| Purpose | File |
|---------|------|
| Wire pipeline to API | `backend/api_server.py` → `handle_message()` |
| Unblock flow (intake complete) | `backend/agents/intake_agent.py` → `process()` |
| Orchestrator flow & branching | `backend/orchestrator.py` |
| Red-flag list | `backend/data/red_flags.json` |
| Triage/routing rules | `backend/data/clinic_rules.json` |
| Test cases & checklist | `docs/test_scenarios.md` |
| Full roadmap | `PROJECT_PLAN.md` |
| Run backend | `cd backend && python api_server.py` |
| Env vars | `.env` from `.env.example` (OPENAI_API_KEY, PORT, etc.) |

---

## Summary

1. **Wire** `api_server.py` → Orchestrator in `handle_message()`.
2. **Unblock** Intake (simple rule or LLM) so `intake_complete: True` when species + chief complaint are present.
3. **Smoke test** locally: one message end-to-end, no 500, real triage/guidance.
4. **Validate** with test scenarios 1–4 (emergency, toxin, routine, ambiguous).
5. **Harden** (language, voice, n8n, errors, Docker) then run evaluation and complete report + video.

After Phase A and B you have a working, safety-correct POC. Phases C and D make it demo-ready and assignment-complete.
