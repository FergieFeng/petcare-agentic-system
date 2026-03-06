# Next Steps to Build the PetCare POC

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview | **Date:** March 1, 2026

**Due date:** March 22, 2026 · **Target build complete:** March 10–11, 2026 · *Last updated: March 6, 2026*

**POC plan alignment:** Steps 1–9 are **done**. All consumer features are **built**. Deployment is **Render** ([DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)). Webhook/n8n is **optional** for POC.

This document is the **action plan** for the POC build. Steps 1–9 are **done**; the pipeline runs end-to-end with 100% M2/M4 accuracy. All consumer-ready features, frontend redesign, auth, and deployment are complete. Remaining: report + demo video (Step 10).

---

## Plan update (March 2026)

**Done:** Design, architecture, and code updated to incorporate feedback:

- **Text-first MVP** — Documented in README, AGENT_DESIGN_CANVAS, scope_and_roles, BASELINE_METHODOLOGY. Voice is optional; baseline evaluation is text-based.
- **Baseline comparison** — Manual receptionist phone script (Option 1); same test scenarios and four metrics for both baseline and agent.
- **Four metrics** — Time to complete intake, required fields captured (>90%), triage accuracy (>80%), red-flag detection (100%) are in design docs and BASELINE_METHODOLOGY; architecture doc describes where each is measured.
- **Code for evaluation** — Session has `first_message_at`; `GET /api/session/<id>/summary` returns `evaluation_metrics` (required_fields_captured_pct, red_flag_triggered, triage_urgency_tier, timestamps). Confidence Gate outputs `required_fields_captured_pct` for M1.

**Immediate next steps:** Steps 1–7 done (including Render deployment path). Remaining: Evaluation polish (9), Report + demo video (10). Step 6 (voice) and Step 8 (webhook/n8n) are optional for MVP.

---

## Current State (as of March 6, 2026)

| Component | Status | Details |
|-----------|--------|---------|
| **API server** | ✅ Done | Flask + Gunicorn, HTTP Basic Auth (env vars only), two-tier sessions |
| **Orchestrator** | ✅ Done | Full flow A→B→C→D→E→F→G; emergency branch; clarification loop |
| **Intake Agent (A)** | ✅ Done | GPT-4o-mini; adaptive follow-ups; any animal species |
| **Safety Gate (B)** | ✅ Done | Rule-based; 50+ red flags; 100% M4 detection |
| **Confidence Gate (C)** | ✅ Done | Rule-based; REQUIRED_FIELDS, action thresholds |
| **Triage (D)** | ✅ Done | GPT-4o-mini; 100% M2 accuracy on 6 scenarios |
| **Routing (E)** | ✅ Done | Rule-based; reads `clinic_rules.json` |
| **Scheduling (F)** | ✅ Done | Rule-based; reads `available_slots.json` |
| **Guidance & Summary (G)** | ✅ Done | GPT-4o-mini; species-correct guidance; 7 languages |
| **Frontend** | ✅ Done | Warm teal theme, Inter font, dark mode, RTL, PWA |
| **Consumer features** | ✅ Done | Streaming, vet finder, PDF, photo, profiles, history, cost, feedback, reminders, breed risks, onboarding, transcript export, consent banner |
| **Voice** | ✅ Done | Tier 1 (Browser) + Tier 2 (Whisper/TTS); Tier 3 stretch |
| **7 languages** | ✅ Done | EN, FR, ZH, AR, ES, HI, UR with full UI translation |
| **Auth** | ✅ Done | HTTP Basic Auth (env vars only, never hardcoded) |
| **Session persistence** | ✅ Done | Two-tier: active 1hr + completed 24hr for PDF |
| **Docker + Gunicorn** | ✅ Done | Production-ready Dockerfile with health check |
| **Webhook** | ✅ Done | Optional; fires if `N8N_WEBHOOK_URL` set |
| **Data files** | ✅ Wired | clinic_rules.json, red_flags.json, available_slots.json |
| **Deployment** | ✅ Render-ready | Deployment guides complete |
| **Documentation** | ✅ Done | All docs updated to match current POC |

**POC status:** Pipeline runs end-to-end. 100% M2 triage, 100% M4 red-flag. ~11.4s avg processing. Deploy via Render per [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).

**From Diana's branch (merged):** Baseline evaluation methodology is documented in [BASELINE_METHODOLOGY.md](docs/BASELINE_METHODOLOGY.md) — manual receptionist script (Baseline-1), M1–M6 metrics, gold labels, and comparison procedure for evaluation (Step 9 below).

**MVP scope:** Ship **text-first**; voice is optional and must not block demo or baseline comparison. Evaluation uses four metrics for both baseline and agent: time to complete intake, required fields captured (>90%), triage accuracy (>80%), red-flag detection (100%).

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

- Call OpenAI with a system prompt that: extracts species, chief complaint, timeline, and symptom details; never diagnoses; responds in the session language.
- From the LLM response, populate `pet_profile`, `chief_complaint`, `symptom_details` and set `intake_complete: True` when required fields (e.g. species + chief_complaint) are present; otherwise return `follow_up_questions`.
- Pass `session['language']` into the prompt so the assistant and follow-up questions use the correct language.

**Success:** For a message like “My dog has been vomiting for 2 days and isn’t eating,” the pipeline runs A → B → C → D → E → F → G and returns triage + guidance + (if implemented) slot options.

### Step 3: Smoke Test Locally

1. Copy `.env.example` to `.env` and set `OPENAI_API_KEY`.
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

## After team testing: report writing and demo recording from Render

Once the team has finished testing (scenarios validated, evaluation metrics run, 1 strong + 1 failure case noted):

1. **Report writing**  
   Complete `technical_report.md`: executive summary, end-to-end description, key results, trade-offs, risks and mitigations, viability beyond POC. Use the test results and screenshots from the Render app in the appendix.

2. **Demo recording**  
   Record the **10–15 minute POC demo video** using the **live app on Render** (not localhost):
   - Open the Render deployment URL in the browser.
   - Record the screen while you: state problem and value proposition, walk through 2–3 realistic scenarios (e.g. emergency, routine, ambiguous), show results and learnings (strong example + failure), and mention next steps.
   - This keeps the demo consistent and shareable (reviewers can try the same URL).

3. **Final polish**  
   Update README with the live Render URL in the “Live Demo” section, ensure all next-step checkboxes reflect current status, and submit by **March 22, 2026**.

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
| Baseline evaluation (Diana) | `docs/BASELINE_METHODOLOGY.md` — M1–M6, gold labels, comparison procedure |
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
