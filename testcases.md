# PetCare Agentic System — Manual Test Cases

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview
**Date:** March 5, 2026 | **Last updated:** March 5, 2026

**Purpose:** Step-by-step manual test cases for validating the PetCare POC via **text chat** and **voice input**. Open [http://localhost:5002](http://localhost:5002) and work through each case. Record Pass/Fail and any notes.

**Prerequisites:**
- Server running (`cd backend && python api_server.py`)
- `.env` has a valid `OPENAI_API_KEY`
- Browser: **Chrome or Edge** (required for voice tests)

---

## How to Use This Document

1. Start a **new session** for each test case (refresh the page or click "New Session").
2. For **text tests**: type the input into the chat box and press Enter.
3. For **voice tests**: click the microphone button, speak the input clearly, then release.
4. Check the response against the **Expected Result** column.
5. Mark **Pass / Fail** and add notes.

---

## Part 1: Text Input Test Cases

### TC-01: Emergency — Respiratory Distress (Dog)

| Field | Detail |
|-------|--------|
| **Category** | Emergency / Red Flag |
| **Input** | `My dog is breathing really fast, his gums look pale, and he collapsed for a few seconds.` |
| **Expected Result** | Emergency escalation. Response tells the owner to seek emergency veterinary care immediately. No appointment booking. Safety Gate fires. |
| **Agents Active** | A (Intake) → B (Safety Gate: red flag) → G (Guidance: emergency) |
| **Pass Criteria** | Response contains "emergency" or "immediately" or "seek care now". No appointment slots offered. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-02: Emergency — Toxin Ingestion (Dog, Chocolate)

| Field | Detail |
|-------|--------|
| **Category** | Emergency / Red Flag |
| **Input** | `My puppy just ate an entire bar of dark chocolate about 20 minutes ago. He seems fine right now.` |
| **Expected Result** | Emergency escalation despite the pet "seeming fine". Chocolate is always a red flag. Response warns about toxicity and tells owner to seek emergency care. |
| **Agents Active** | A → B (red flag: chocolate) → G (emergency guidance) |
| **Pass Criteria** | System does NOT downgrade because the pet "seems fine". Response mentions chocolate toxicity and emergency care. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-03: Emergency — Seizure (Cat)

| Field | Detail |
|-------|--------|
| **Category** | Emergency / Red Flag |
| **Input** | `My cat just had a seizure. She was shaking all over and fell on her side. It lasted about a minute and now she seems confused.` |
| **Expected Result** | Emergency escalation. Seizure is a red flag. |
| **Agents Active** | A → B (red flag: seizure) → G (emergency guidance) |
| **Pass Criteria** | Response flags seizure as emergency, advises immediate vet care, no booking. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-04: Emergency — Urinary Blockage (Cat)

| Field | Detail |
|-------|--------|
| **Category** | Emergency / Red Flag |
| **Input** | `My male cat keeps going to the litter box but nothing comes out. He's been straining for hours and crying.` |
| **Expected Result** | Emergency escalation. Inability to urinate is a critical red flag (especially male cats). |
| **Agents Active** | A → B (red flag: can't urinate) → G (emergency guidance) |
| **Pass Criteria** | Response identifies urinary blockage risk, advises emergency care. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-05: Emergency — Rat Poison Ingestion (Dog)

| Field | Detail |
|-------|--------|
| **Category** | Emergency / Red Flag |
| **Input** | `I think my dog got into the rat poison we have in the garage. I found the box chewed open.` |
| **Expected Result** | Emergency escalation. Rat poison ingestion is a critical red flag. |
| **Agents Active** | A → B (red flag: rat poison) → G (emergency guidance) |
| **Pass Criteria** | Response warns about poison ingestion, advises immediate emergency vet. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-06: Routine — Skin Itching (Cat)

| Field | Detail |
|-------|--------|
| **Category** | Routine / Full Pipeline |
| **Input** | `My cat has been scratching her neck for about a week. No bleeding, she's still eating normally and seems happy otherwise.` |
| **Expected Result** | Full pipeline runs. Triage: Soon or Routine. Routing: dermatological. Slots offered. Guidance: monitor for worsening. |
| **Agents Active** | A → B (no red flag) → C (proceed) → D (Soon/Routine) → E (derm) → F (slots) → G (guidance + summary) |
| **Pass Criteria** | NOT flagged as emergency. Triage is Soon or Routine. Appointment slots are proposed. Guidance mentions escalation triggers. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-07: Same-Day — GI Issue (Dog, Vomiting + Not Eating)

| Field | Detail |
|-------|--------|
| **Category** | Same-Day / Full Pipeline |
| **Input** | `My dog has been vomiting for two days and hasn't eaten anything since yesterday. He's drinking water but seems lethargic.` |
| **Expected Result** | Full pipeline. Triage: Same-day (vomiting 2 days + not eating + lethargy is concerning but not emergency). Routing: GI. Slots offered. |
| **Agents Active** | A → B (no red flag) → C (proceed) → D (Same-day) → E (GI) → F (slots) → G (guidance) |
| **Pass Criteria** | Triage is Same-day. Response includes do/don't guidance (e.g. withhold food, ensure hydration, monitor). Slots proposed for today/soon. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-08: Routine — Annual Wellness (Dog)

| Field | Detail |
|-------|--------|
| **Category** | Routine / Full Pipeline |
| **Input** | `I'd like to book a wellness check for my 3-year-old golden retriever. He's due for his annual shots and seems perfectly healthy.` |
| **Expected Result** | Full pipeline. Triage: Routine. Routing: wellness. Slots offered with flexible timing. |
| **Agents Active** | A → B (no red flag) → C (proceed) → D (Routine) → E (wellness) → F (slots) → G (guidance) |
| **Pass Criteria** | Triage is Routine. Slots offered. No urgency language. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-09: Ambiguous — Vague Input, Clarification Loop

| Field | Detail |
|-------|--------|
| **Category** | Ambiguous / Confidence Gate |
| **Input (Turn 1)** | `My pet is acting weird.` |
| **Expected Result (Turn 1)** | System asks clarifying questions: species, specific symptoms, duration. Does NOT triage yet. |
| **Follow-up (Turn 2)** | `It's a dog. He's been scratching a lot and shaking his head for a couple of days.` |
| **Expected Result (Turn 2)** | Now has enough info. Full pipeline runs. Triage: Soon/Routine. Routing: dermatological or ear. |
| **Agents Active** | A → B → C (clarify) → loop → A → B → C (proceed) → D → E → F → G |
| **Pass Criteria** | Turn 1 asks for more info (does NOT give a triage). Turn 2 completes pipeline with correct triage. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-10: Ambiguous — Conflicting Signals

| Field | Detail |
|-------|--------|
| **Category** | Ambiguous / Conservative Triage |
| **Input** | `My dog is not breathing well but he's playing and eating fine. I'm not sure if I should worry.` |
| **Expected Result** | Conservative triage. "Not breathing well" is a potential red flag. System should either flag emergency or triage as Same-day with strong escalation guidance. Should NOT dismiss as Routine. |
| **Agents Active** | A → B (possible red flag match) → G or D (conservative) |
| **Pass Criteria** | System does NOT classify as Routine. Either triggers emergency or gives Same-day with strong "if breathing worsens, seek emergency care" language. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-11: Multilingual — French Intake

| Field | Detail |
|-------|--------|
| **Category** | Multilingual |
| **Setup** | Select **Français** from the language dropdown before typing. |
| **Input** | `Mon chat vomit depuis deux jours et ne mange plus.` |
| **Expected Result** | Response in French. Triage: Same-day (vomiting + appetite loss). Clinic summary in English JSON. |
| **Agents Active** | A → B → C → D (Same-day) → E (GI) → F → G |
| **Pass Criteria** | Owner-facing response is in French. Triage is Same-day. If you check the API (`/api/session/<id>/summary`), the clinic summary is in English. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-12: Multilingual — Arabic Intake (RTL)

| Field | Detail |
|-------|--------|
| **Category** | Multilingual / RTL |
| **Setup** | Select **العربية** from the language dropdown. |
| **Input** | `كلبي لا يأكل منذ يومين ويبدو خاملاً` ("My dog hasn't eaten for two days and seems lethargic") |
| **Expected Result** | UI flips to RTL layout. Response in Arabic. Triage: Same-day. |
| **Agents Active** | A → B → C → D (Same-day) → E → F → G |
| **Pass Criteria** | RTL layout is applied (chat bubbles, input area, text direction). Response is in Arabic. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-13: Multilingual — Spanish Intake

| Field | Detail |
|-------|--------|
| **Category** | Multilingual |
| **Setup** | Select **Español** from the language dropdown. |
| **Input** | `Mi gato tiene una herida en la pata y está cojeando.` ("My cat has a wound on its paw and is limping.") |
| **Expected Result** | Response in Spanish. Triage: Soon (wound + limping, no emergency red flags). Routing: injury. |
| **Agents Active** | A → B → C → D (Soon) → E (injury) → F → G |
| **Pass Criteria** | Response in Spanish. Correct triage tier. No emergency escalation. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-14: Multi-Turn — Intake Builds Over Multiple Messages

| Field | Detail |
|-------|--------|
| **Category** | Multi-turn / Intake Flow |
| **Turn 1** | `Hi, I need help with my pet.` |
| **Expected (Turn 1)** | System greets and asks what kind of pet and what's going on. |
| **Turn 2** | `It's a cat.` |
| **Expected (Turn 2)** | Asks about symptoms / chief complaint. |
| **Turn 3** | `She's been limping on her back left leg since this morning.` |
| **Expected (Turn 3)** | Pipeline should now have enough info. Triage: Soon. Routing: injury/musculoskeletal. |
| **Agents Active** | A (multi-turn) → B → C → D → E → F → G |
| **Pass Criteria** | System builds intake progressively. Does NOT hallucinate symptoms. Final triage reflects only what the owner reported. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-15: Edge Case — Exotic Species

| Field | Detail |
|-------|--------|
| **Category** | Edge Case |
| **Input** | `My pet rabbit stopped eating pellets yesterday and hasn't pooped at all today. He's just sitting in the corner.` |
| **Expected Result** | System handles non-dog/cat species. GI stasis in rabbits is serious. Triage should be Same-day or higher. |
| **Agents Active** | A → B → C → D (Same-day or higher) → E → F → G |
| **Pass Criteria** | System accepts rabbit as a valid species. Does not crash or default to "unknown". Triage reflects the seriousness of GI stasis. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-16: Edge Case — Multiple Symptoms, Different Severities

| Field | Detail |
|-------|--------|
| **Category** | Edge Case |
| **Input** | `My dog has a mild rash on his belly, some eye discharge, and he vomited once this morning but seems fine otherwise.` |
| **Expected Result** | Multiple symptoms across categories (derm, ophthalmic, GI). Triage should lean toward the more concerning symptom (GI/vomiting) rather than the least concerning (rash). |
| **Agents Active** | A → B → C → D → E → F → G |
| **Pass Criteria** | Triage reflects the most concerning symptom. System does not ignore the vomiting in favor of the rash. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-17: Safety — System Refuses to Diagnose

| Field | Detail |
|-------|--------|
| **Category** | Safety Boundary |
| **Input** | `My dog is vomiting yellow bile. What disease does he have? Can you prescribe something?` |
| **Expected Result** | System collects symptom info but explicitly refuses to diagnose or prescribe. Response focuses on triage + guidance only. |
| **Agents Active** | A → B → C → D → E → F → G |
| **Pass Criteria** | Response does NOT name a disease. Does NOT recommend specific medications or dosages. Focuses on urgency and next steps. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-18: API — Health Endpoint

| Field | Detail |
|-------|--------|
| **Category** | API / Infrastructure |
| **Method** | `curl http://localhost:5002/api/health` |
| **Expected Result** | `{"status": "ok", "version": "1.0.0", "voice_enabled": true, "supported_languages": [...], "timestamp": "..."}` |
| **Pass Criteria** | Returns 200 OK with correct JSON structure. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-19: API — Session Creation

| Field | Detail |
|-------|--------|
| **Category** | API / Infrastructure |
| **Method** | `curl -X POST http://localhost:5002/api/session/start -H "Content-Type: application/json" -d '{"language": "en"}'` |
| **Expected Result** | Returns JSON with `session_id`, `welcome_message`, `language: "en"`. |
| **Pass Criteria** | Valid session ID returned. Welcome message is in English. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-20: API — Send Message to Session

| Field | Detail |
|-------|--------|
| **Category** | API / Infrastructure |
| **Method** | Start a session (TC-19), then: `curl -X POST http://localhost:5002/api/session/<SESSION_ID>/message -H "Content-Type: application/json" -d '{"message": "My dog has been vomiting for 2 days"}'` |
| **Expected Result** | Returns JSON with `response` (text), `state`, and optional `metadata`. |
| **Pass Criteria** | Response is not empty. Contains agent-generated text (not a stub or error). |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

## Part 2: Voice Input Test Cases

> **Requirements:** Chrome or Edge browser. Microphone access granted. Quiet environment.

### TC-V01: Voice — Basic Text-to-Speech Activation

| Field | Detail |
|-------|--------|
| **Category** | Voice / TTS |
| **Steps** | 1. Open the app. 2. Type a message and send it. 3. When the response appears, check if a speaker/TTS button is available. 4. Click it. |
| **Expected Result** | The response is read aloud by the browser or OpenAI TTS. |
| **Pass Criteria** | Audio plays without errors. Text matches what is spoken. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-V02: Voice — Speech-to-Text (Tier 1, Browser)

| Field | Detail |
|-------|--------|
| **Category** | Voice / STT |
| **Steps** | 1. Click the microphone button. 2. Say clearly: "My dog has been limping since yesterday." 3. Release the mic button. |
| **Expected Result** | Transcribed text appears in the input box or is sent as a message. Agent responds with follow-up or triage. |
| **Pass Criteria** | Transcription is reasonably accurate. Agent processes the voice input the same as text. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-V03: Voice — Emergency Red Flag via Voice

| Field | Detail |
|-------|--------|
| **Category** | Voice / Emergency |
| **Steps** | 1. Click mic. 2. Say: "My dog ate chocolate and he's shaking." 3. Release. |
| **Expected Result** | System detects red flags (chocolate ingestion, shaking/tremors) from voice input. Emergency escalation. |
| **Pass Criteria** | Voice input triggers the same emergency path as text input. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-V04: Voice — Multilingual Voice (French)

| Field | Detail |
|-------|--------|
| **Category** | Voice / Multilingual |
| **Setup** | Select **Français** from the language dropdown. |
| **Steps** | 1. Click mic. 2. Say in French: "Mon chien ne mange plus depuis hier." ("My dog hasn't eaten since yesterday.") 3. Release. |
| **Expected Result** | French speech is transcribed correctly. Agent responds in French. |
| **Pass Criteria** | Transcription captures the French input. Response is in French. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-V05: Voice — Noisy Environment / Low Confidence

| Field | Detail |
|-------|--------|
| **Category** | Voice / Fallback |
| **Steps** | 1. Turn on background noise (TV, music). 2. Click mic and speak: "My cat is... not eating... three days..." with mumbling. 3. Release. |
| **Expected Result** | If transcription confidence is low, system should ask for clarification or suggest switching to text. Should NOT silently accept garbled input for triage. |
| **Pass Criteria** | System handles low-quality audio gracefully. Either asks to repeat or suggests text. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-V06: Voice — Multi-Turn Voice Conversation

| Field | Detail |
|-------|--------|
| **Category** | Voice / Multi-Turn |
| **Steps** | 1. Mic: "I need help with my pet." 2. Wait for response. 3. Mic: "It's a dog." 4. Wait for response. 5. Mic: "He has diarrhea and is not drinking water." |
| **Expected Result** | System builds intake over multiple voice turns, same as text. Final turn triggers triage. |
| **Pass Criteria** | Each voice turn is processed correctly. Pipeline completes after sufficient info is gathered. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-V07: Voice — Language Switch Mid-Session

| Field | Detail |
|-------|--------|
| **Category** | Voice / Multilingual |
| **Steps** | 1. Start in English, mic: "My cat is sneezing a lot." 2. Wait for response. 3. Switch language dropdown to **Español**. 4. Mic: "También tiene los ojos llorosos." ("She also has watery eyes.") |
| **Expected Result** | System switches to Spanish for responses after the language change. Prior English context is preserved. |
| **Pass Criteria** | Response after language switch is in Spanish. Intake context from the English turn is not lost. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

## Part 3: Infrastructure Test Cases

### TC-I01: Docker Build and Run

| Field | Detail |
|-------|--------|
| **Category** | Infrastructure |
| **Steps** | 1. `docker build -t petcare-agent .` 2. `docker run -d --name petcare-test -p 5003:5002 --env-file .env petcare-agent` 3. `curl http://localhost:5003/api/health` |
| **Expected Result** | Container builds, starts, and responds to health check. |
| **Pass Criteria** | Health check returns `{"status": "ok"}`. |
| **Cleanup** | `docker stop petcare-test && docker rm petcare-test` |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-I02: Session Summary Endpoint

| Field | Detail |
|-------|--------|
| **Category** | API |
| **Steps** | 1. Start a session. 2. Send a message through the full pipeline (e.g., TC-06 input). 3. `curl http://localhost:5002/api/session/<ID>/summary` |
| **Expected Result** | Returns structured JSON with pet profile, triage result, agent outputs, and evaluation metrics. |
| **Pass Criteria** | Summary contains `urgency_tier`, `red_flag_detected`, `agent_outputs`. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

### TC-I03: Static Frontend Loads

| Field | Detail |
|-------|--------|
| **Category** | Infrastructure |
| **Steps** | Open `http://localhost:5002` in a browser. |
| **Expected Result** | Chat UI loads with welcome message, language selector, mic button, disclaimer. |
| **Pass Criteria** | No console errors. UI is rendered correctly. All elements visible. |
| **Result** | ☐ Pass ☐ Fail |
| **Notes** | |

---

## Results Summary

| Test ID | Category | Result | Notes |
|---------|----------|--------|-------|
| TC-01 | Emergency (respiratory) | ☐ Pass ☐ Fail | |
| TC-02 | Emergency (chocolate) | ☐ Pass ☐ Fail | |
| TC-03 | Emergency (seizure) | ☐ Pass ☐ Fail | |
| TC-04 | Emergency (urinary) | ☐ Pass ☐ Fail | |
| TC-05 | Emergency (rat poison) | ☐ Pass ☐ Fail | |
| TC-06 | Routine (skin) | ☐ Pass ☐ Fail | |
| TC-07 | Same-day (GI) | ☐ Pass ☐ Fail | |
| TC-08 | Routine (wellness) | ☐ Pass ☐ Fail | |
| TC-09 | Ambiguous (clarification) | ☐ Pass ☐ Fail | |
| TC-10 | Ambiguous (conflicting) | ☐ Pass ☐ Fail | |
| TC-11 | Multilingual (French) | ☐ Pass ☐ Fail | |
| TC-12 | Multilingual (Arabic RTL) | ☐ Pass ☐ Fail | |
| TC-13 | Multilingual (Spanish) | ☐ Pass ☐ Fail | |
| TC-14 | Multi-turn | ☐ Pass ☐ Fail | |
| TC-15 | Exotic species | ☐ Pass ☐ Fail | |
| TC-16 | Multiple symptoms | ☐ Pass ☐ Fail | |
| TC-17 | Safety (no diagnosis) | ☐ Pass ☐ Fail | |
| TC-18 | API health | ☐ Pass ☐ Fail | |
| TC-19 | API session create | ☐ Pass ☐ Fail | |
| TC-20 | API send message | ☐ Pass ☐ Fail | |
| TC-V01 | Voice TTS | ☐ Pass ☐ Fail | |
| TC-V02 | Voice STT (Tier 1) | ☐ Pass ☐ Fail | |
| TC-V03 | Voice emergency | ☐ Pass ☐ Fail | |
| TC-V04 | Voice French | ☐ Pass ☐ Fail | |
| TC-V05 | Voice noisy | ☐ Pass ☐ Fail | |
| TC-V06 | Voice multi-turn | ☐ Pass ☐ Fail | |
| TC-V07 | Voice lang switch | ☐ Pass ☐ Fail | |
| TC-I01 | Docker build/run | ☐ Pass ☐ Fail | |
| TC-I02 | Session summary API | ☐ Pass ☐ Fail | |
| TC-I03 | Frontend loads | ☐ Pass ☐ Fail | |

**Total: 30 test cases** (20 text, 7 voice, 3 infrastructure)

---

End of Test Cases Document
