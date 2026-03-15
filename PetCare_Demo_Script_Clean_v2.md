
PetCare Demo Script — Clean V2 (12–13 minutes)

Team Broadview
MMAI 891 — Assignment 3

App:
https://petcare-agentic-system.onrender.com

Repo:
https://github.com/FergieFeng/petcare-agentic-system

1. Problem & Value Proposition (≈1.5 min)

Veterinary clinics spend significant time on intake phone calls. A typical intake call takes about five minutes. A receptionist collects pet information, judges urgency, selects an appointment type, and explains next steps to a worried owner.

The quality of this process varies by staff experience. When urgency is misjudged, the clinic often has to rebook the appointment, wasting time for both staff and pet owners.

Our project explores whether an AI agent can automate that intake workflow.

PetCare is a proof‑of‑concept triage and smart booking agent that:
- collects pet information
- detects emergencies
- classifies urgency
- routes to the correct appointment type
- generates guidance for the owner

This project was developed by Team Broadview.

2. Agent Workflow Overview (≈1 min)

The system is structured as a seven‑step agent workflow:

1. Intake Agent – collects pet and symptom information
2. Safety Gate – checks emergency red flags
3. Confidence Gate – verifies enough information
4. Triage Agent – classifies urgency
5. Routing Agent – selects appointment type
6. Scheduling Agent – proposes appointment slots
7. Guidance Agent – generates instructions and a clinic summary

Only three agents call the LLM. The other four use rule‑based logic to reduce hallucination risk and keep latency low.

3. Live Demo — Emergency Scenario (≈3 min)

Prompt:
"My dog ate a whole bar of dark chocolate about an hour ago."

Key points to highlight:
• Emergency alert card appears
• No appointment slots offered
• Immediate emergency guidance
• Nearby vet finder

Explanation:

The Safety Gate performs deterministic red‑flag detection using veterinary emergency keywords. If a red flag is detected, the workflow short‑circuits and immediately escalates to emergency guidance. This prevents the LLM from under‑triaging a life‑threatening case.

4. Live Demo — Full Workflow (≈3 min)

Prompt:
"My cat has been vomiting for two days and hasn't eaten much."

Walk through:
• Intake clarification
• Triage result
• Appointment routing
• Scheduling suggestions
• Owner guidance
• PDF clinic summary

Explanation:

This demonstrates the full pipeline from intake to booking. The workflow completes in roughly eight seconds using three LLM calls.

5. Multilingual Capability (≈1 min)

Switch the interface to Chinese.

Prompt:
"我的狗狗今天呕吐了三次，不吃东西。"

Highlight:
• Intake response appears in Chinese
• Urgency label localized
• Guidance block localized

Explanation:

The system supports seven languages. Backend logic remains language‑agnostic while responses are localized for the user.

6. Testing & Evaluation (≈1 min)

Evaluation used a synthetic test set of veterinary intake scenarios including emergencies, routine visits, and ambiguous inputs.

Key results:
• 100% triage accuracy across six automated scenarios
• 100% emergency detection
• Average intake time: 8.4 seconds
• Baseline manual intake estimate: ~4 minutes

This suggests substantial potential reduction in administrative workload.

7. Failure Case — TC‑04 (RAG Pivot) (≈2 min)

Prompt:
"My male cat keeps going to the litter box but nothing comes out."

Explanation:

Urinary blockage in male cats is a medical emergency.

In version 1.0 the Safety Gate relied on exact substring matching. Natural phrasing did not match predefined strings, so the case was under‑triaged.

Fix:

We implemented Retrieval Augmented Generation (RAG).

During triage, the complaint is matched against illness entries in the knowledge base. Relevant clinical context is injected into the triage prompt so the model can correctly classify the case as Emergency.

8. Security Testing (≈1 min)

Security testing revealed that the voice synthesis endpoint originally allowed unauthenticated requests.

This meant an attacker could generate audio using our OpenAI account without an active session.

Fix:
• session validation
• authentication checks
• rate limiting

After these fixes, the same pentest script reported all vulnerabilities blocked.

This demonstrates the importance of security testing in AI systems.

9. Limitations & Next Steps (≈1 min)

Current limitations:
• mock scheduling data
• in‑memory session storage
• deterministic safety gate still brittle for phrasing variants
• no real clinic usability study

Next steps:
• fuzzy matching for safety gate
• real scheduling API integration
• Redis/PostgreSQL persistence
• clinic pilot testing

Total demo runtime: approximately 12–13 minutes.
