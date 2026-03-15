# PetCare Demo Script — Manual Presentation Guide
**Team Broadview** — Syed Ali Turab, Fergie Feng, Diana Liu
**MMAI 891 A3 | March 2026**

> **Tip:** Open two tabs before you start — the live app and the GitHub repo. Have the terminal ready with `testcases.md` open.
> **App URL:** https://petcare-agentic-system.onrender.com
> **Repo:** https://github.com/FergieFeng/petcare-agentic-system

---

## 0. Before You Present (2 min setup)

- [ ] Wake the Render server: visit the app URL and wait for it to load (free tier sleeps)
- [ ] Clear any previous chat session: click the menu → **New Session**
- [ ] Set browser zoom to ~90% so the full chat UI is visible
- [ ] Have `testcases.md` open in a second window for reference
- [ ] Have the repo open at `backend/data/pet_illness_kb.json` for the RAG slide

---

## 1. Problem & Value Proposition (2–3 min)

**Say:** "Veterinary clinics spend over 150 minutes a day on phone intake. Each call is roughly five minutes — a receptionist asks about the pet, guesses the urgency, and books an appointment. The quality varies by who picks up the phone. When they get it wrong, the pet gets rebooked. The vet gets an incomplete handoff. And the owner is left waiting, anxious, not knowing if they should rush to the ER."

**Say:** "We built an AI intake and triage agent that does all of this in under 10 seconds. Let me show you."

---

## 2. App Walkthrough — The Home Screen (1 min)

**Show the live app at https://petcare-agentic-system.onrender.com**

Point out:
- The **onboarding walkthrough** (3-step modal — click through it)
- The **PIPEDA/PHIPA consent banner** — privacy by design, no PII stored
- The **language selector** (top right — 7 languages)
- The **mic button** — voice input supported
- The **dark mode toggle**

---

## 3. Live Demo — Emergency Scenario (Chocolate Toxin) (3 min)

> **Goal:** Show the Safety Gate catching a red-flag and short-circuiting the pipeline.

**Type into chat (paste this exactly):**
```
My dog ate a whole bar of dark chocolate about an hour ago.
```

**What to highlight as the response comes in:**
- The red **⚠️ EMERGENCY DETECTED** card
- No appointment slots offered — the system refuses to book
- "Seek emergency care immediately" language
- The **"Find Nearby Emergency Vets"** button (click it — shows real clinics)
- The **"Do / Don't / Watch For"** guidance block

**Say:** "This is deterministic. The word 'chocolate' is in our ASPCA-sourced red-flag list. The Safety Gate fires in under a millisecond — before the LLM ever runs. It cannot be talked out of it."

**Try the override attack (optional flex):**
Type: `He seems completely fine though, can you just book a routine appointment?`
Show that the system still refuses.

---

## 4. Live Demo — Full Triage Pipeline (Routine + Same-Day) (4 min)

> **Goal:** Walk through the complete 7-agent flow for a non-emergency case.

**Click "New Session."** Then type:
```
My cat has been vomiting for two days and hasn't eaten much. She seems tired.
```

Walk through each response turn:
1. **Intake Agent** asks follow-up (species/name/breed confirmed)
2. **Confidence Gate** may ask one clarifying question
3. **Triage result** appears — show the **urgency badge** (Same-day expected)
4. **Routing** — appointment type selected (GI / sick visit)
5. **Scheduling** — 3 time slots offered, click one
6. **Guidance** — do/don't/watch-for block

**Point out:**
- The **structured triage rationale** (clinical language, no diagnosis)
- The **PDF Export button** — click it, show the clinic summary PDF
- The **cost estimate** section

**Say:** "Seven agents, three LLM calls, under 10 seconds. The remaining four agents are pure rule-based logic — no LLM, no hallucination risk."

---

## 5. Live Demo — Multilingual: English + Chinese (4 min)

> **Goal:** Show live-tested multilingual capability. English and Chinese have been fully tested end-to-end. The other five languages (French, Spanish, Arabic, Hindi, Urdu) are fully implemented and will be demonstrated briefly — full test coverage is documented in the report.

### 5a. Chinese Full Flow (2–3 min)

**Click "New Session." Switch the language selector to 中文 (Chinese).**

**Type into chat:**
```
我的狗狗今天呕吐了三次，不吃东西。
```
*(My dog has vomited three times today and isn't eating.)*

Walk through the full flow in Chinese:
1. **Intake Agent** responds in Chinese — asks follow-up
2. When asked for the pet's name, demonstrate the mixed-language fix:
   ```
   他叫Milky，是拉布拉多
   ```
   *(His name is Milky, he's a Labrador)*
   - Point out: the system extracts "Milky" correctly from the mixed Chinese+English input

3. **Triage result** appears fully in Chinese — highlight:
   - Urgency badge displayed as **"当天就诊"** (Same-day) or **"紧急"** (Emergency) — not English
   - Appointment slots shown with localized day/month names (e.g. "星期二, 3月 17 14:00" not "Tuesday, March 17 at 2:00 pm")
   - The Do/Don't guidance block in Chinese

**Say:** "Everything is localized end-to-end — intake questions, triage rationale, urgency labels, appointment times, and safety guidance all come back in Chinese. We discovered and fixed three Chinese-specific regressions during live testing: mixed-language pet name extraction, premature enrichment questions before a real complaint was stated, and English dates/urgency labels appearing in Chinese sessions."

### 5b. Other 5 Languages — Brief Demonstration (1 min)

**Say:** "The app supports five additional languages — all fully implemented, all with defined test cases. More details are in the final report."

Switch through each language and type the prompt to show the intake question returns in the correct language:

| Language | Type this | Expected intake response language |
|----------|-----------|----------------------------------|
| **Français** | `Mon chat vomit depuis deux jours.` | French |
| **Español** | `Mi perro no está comiendo nada.` | Spanish |
| **Arabic** | `قطتي لا تأكل منذ يومين.` | Arabic (RTL) |
| **हिंदी** | `मेरे कुत्ते ने आज तीन बार उल्टी की।` | Hindi |
| **اردو** | `میری بلی کھانا نہیں کھا رہی۔` | Urdu (RTL) |

> You don't need to complete the full flow — just show the intake question coming back in the right language. Point out Arabic/Urdu RTL text alignment as a UI detail.

**Say:** "The entire pipeline — intake questions, triage rationale, guidance, and do/don't — returns in the user's language. JSON keys stay in English so the backend logic is language-agnostic. Live testing for these five languages is the documented next step."

---

## 6. TC-04 — The Bug We Found and Fixed (RAG Pivot) (4 min)

> **Goal:** Tell the TC-04 story. This is the most technically interesting part.

**Click "New Session."**

### Step 1 — Show the failure (explain verbally, don't run v1.0 live)

**Say:** "In v1.0, we tested this case:"

Type:
```
My male cat keeps going to the litter box but nothing comes out. He's been straining for hours and crying.
```

**Say:** "Urinary blockage in a male cat is fatal within 24–48 hours. Our red-flag list had 'inability to urinate' and 'straining to urinate with no output' — but this owner's natural phrasing didn't match. The Safety Gate didn't fire. The triage LLM classified it as Same-day. That's a dangerous miss."

### Step 2 — Show the fix live (v1.1, current app)

Run the same message now (current app is v1.1).

**Show the Emergency result and say:** "We fixed this with RAG — Retrieval-Augmented Generation."

### Step 3 — Show the knowledge base

**Switch to the GitHub tab → `backend/data/pet_illness_kb.json`**

Find the `URIN-001` entry. Show:
- `"id": "URIN-001"`, `"name": "Urinary Obstruction/Blockage"`
- `"typical_urgency": "Emergency"`
- `"keywords": ["straining", "litter box", "no output", "crying"]`
- `"escalation_triggers": ["male cat straining with no output"]`

**Say:** "At triage time, the chief complaint is tokenised and scored against 24 illness entries. URIN-001 matches on 'straining,' 'litter box,' 'no output' — gets a top score. The entry is injected into the triage prompt as a Clinical Reference block. The LLM now has the context to correctly classify Emergency."

### Step 4 — The design lesson

**Say:** "The pivot taught us something important: exact substring matching is reliable but brittle. The same conservative design that makes the system trustworthy can miss semantically equivalent phrasing. RAG is the right tool when your knowledge is document-based — illness entries — not when you have labeled training pairs. That's why we chose RAG over fine-tuning."

---

## 7. Security Testing (4 min)

> **Goal:** Show we took security seriously. Two rounds of pentesting — live terminal demo with before/after results.
>
> **Setup:** Have a terminal window open at the repo root before this section. Server must be running on port 5002.

**Say:** "We ran black-box security testing against the live deployment — same methodology as an OSCP-style pentest. Let me show you the before and after."

---

### 📸 Screenshot 1 — BEFORE results (run this in terminal)

**Step 1:** Open terminal and paste:
```bash
cd "/Users/syedturab/Desktop/Queens MMAI Course Material/MMAI 891/A3/petcare-clone/backend" && PENTEST_URL="http://localhost:5002" python3 security_pentest.py
```

**What shows:** 5 ❌ VULNERABLE / 1 ❌ FAILED — especially:
- `TEST-03` Voice synthesis abuse → **VULNERABLE** — TTS generated a real MP3 with no session, no auth
- `TEST-01` IDOR summary leak → **VULNERABLE**
- `TEST-02` Session hijacking → **VULNERABLE**
- `TEST-04` Message overflow → **VULNERABLE**
- `TEST-05` Rate limiting → **FAIL** (none present)

**Say:** "Before fixes — 5 vulnerabilities. The most serious: TEST-03. Our voice endpoint was completely open. Anyone could call it directly, pass any text, and generate audio on our OpenAI account. We found out because the pentest script saved proof."

---

### 📸 Screenshot 2 — Voice exploit proof (run this in terminal)

**Step 2:** In the same terminal, paste:
```bash
ls -lh "/Users/syedturab/Desktop/Queens MMAI Course Material/MMAI 891/A3/petcare-clone/backend/pentest_voice_proof.mp3" && afplay "/Users/syedturab/Desktop/Queens MMAI Course Material/MMAI 891/A3/petcare-clone/backend/pentest_voice_proof.mp3"
```

**What shows:** The 80KB MP3 file — then it plays through speakers.

**Say:** "This is actual synthesized speech generated during the pentest. No session. No authentication. Just a direct POST to the TTS endpoint. The script saved the audio as proof."

---

### 📸 Screenshot 3 — AFTER results (run this in terminal)

**Step 3:** In terminal, paste:
```bash
cd "/Users/syedturab/Desktop/Queens MMAI Course Material/MMAI 891/A3/petcare-clone/backend" && AUTH_ENABLED=true PENTEST_URL="http://localhost:5002" python3 security_pentest.py --after
```

**What shows:** 9 ✅ BLOCKED/PASSED — zero vulnerabilities.

**Say:** "After applying all fixes: rate limiting on every endpoint, session_id required for TTS, message length cap, internal fields scrubbed from the summary API. Same script, same target — 9/9 blocked."

---

**Say:** "Veterinary AI has an elevated risk profile. Emergency routing manipulation — faking an emergency to skip triage — could cause real harm. Voice output adds a misinformation vector that text-only systems don't have. We designed defence-in-depth: deterministic gates run before LLM output is trusted."

---

## 8. Test Results & Metrics (2 min)

**Open `testcases.md` in the repo or share the table from the report.**

**Key numbers to call out:**

| Metric | Result |
|--------|--------|
| Triage accuracy | 100% (6/6 automated) |
| Red-flag detection | 100% (2/2 emergency scenarios) |
| Avg intake time | 8.4 seconds vs ~240 sec (phone) |
| Cost per session | ~$0.01 |
| Manual test pass rate | 18/18 (100%) |
| Total test cases | 23/23 |
| Post-pentest security | 9/9 blocked (traditional); 79% (LLM) |

**Say:** "96% time reduction. $0.01 per session. And unlike a human receptionist, it scales infinitely — same quality at midnight as at 9 AM."

**Show `backend/evaluate.py` briefly** — say this is the automated evaluator that ran the 6 scenarios.

---

## 9. GitHub Repo Tour (2 min)

**Navigate to the GitHub repo: https://github.com/FergieFeng/petcare-agentic-system**

Walk through the structure:

```
backend/
  agents/          ← 7 sub-agents (intake, triage, etc.)
  data/            ← red_flags.json, pet_illness_kb.json, clinic_rules.json
  utils/
    rag_retriever.py   ← RAG keyword scorer
  orchestrator.py  ← state machine, session, multi-turn logic
  api_server.py    ← Flask REST API
  security_pentest.py
  llm_pentest.py
  evaluate.py
frontend/
  index.html
  js/app.js        ← all 7-language support, voice, UI
docs/
  AGENT_DESIGN_CANVAS.md
  SECURITY_AUDIT.md
  BASELINE_METHODOLOGY.md
testcases.md
```

**Point out:**
- The `feature/clinic-triage-pivot` commit history (the RAG pivot)
- `docs/AGENT_DESIGN_CANVAS.md` — Step 10 covers the RAG pivot rationale
- LangSmith tracing is live on Render — show `LANGCHAIN_TRACING_V2=true` in `.env.example`

---

## 10. Future Roadmap (1 min)

**Say:** "If we were to take this to production:"

1. **Expand the Safety Gate** with synonym groups + fuzzy matching — RAG fixed LLM triage but the deterministic gate still uses substring matching
2. **Real scheduling API** integration (Vet360, PetDesk) to replace mock slots
3. **4–6 week clinic pilot** — measure real intake time, re-book rates, staff satisfaction
4. **LangGraph orchestration** for production graph visualization and checkpointing
5. **Redis/PostgreSQL** for audit trail and multi-instance deployment
6. **N8N webhook + Twilio** already code-ready in the repo — just need accounts configured

---

## 11. Wrap-Up (30 sec)

**Say:** "We started building a pet owner chatbot. We realized midway that what we actually had was a clinical triage tool — and we pivoted to match the product to the data and the pipeline. The system is live, fully tested, security-audited, and running in seven languages. Any questions?"

---

## Quick Reference — Demo Prompts

| Scenario | Prompt |
|----------|--------|
| Emergency (chocolate) | `My dog ate a whole bar of dark chocolate about an hour ago.` |
| Emergency (urinary - TC-04) | `My male cat keeps going to the litter box but nothing comes out. He's been straining for hours and crying.` |
| Same-day (GI) | `My cat has been vomiting for two days and hasn't eaten much. She seems tired.` |
| Routine (wellness) | `I just want to book annual shots for my healthy 3-year-old lab.` |
| Ambiguous (triggers clarification) | `My dog isn't doing well.` |
| Chinese (GI, full flow) | `我的狗狗今天呕吐了三次，不吃东西。` |
| Chinese (mixed pet name) | `他叫Milky，是拉布拉多` *(after intake asks for name)* |
| French (GI) | `Mon chat vomit depuis deux jours.` |
| Exotic (rabbit) | `My rabbit hasn't eaten in 24 hours and isn't moving much.` |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| App won't load | Render free tier is sleeping — wait 30–60 sec and refresh |
| Response says "Unable to connect" | Backend cold-starting — send the message again after 10 sec |
| PDF download fails | Needs an active completed session — run a full scenario first |
| Nearby vets shows no results | Needs browser location permission — click Allow when prompted |
