# Voice Extension Design

**Authors:** Syed Ali Turab & Fergie Feng | **Team:** Broadview | **Date:** March 1, 2026

---

## 1. Purpose

This document defines the Voice Interaction Module for the PetCare Agentic System.

Voice is treated strictly as an interaction-layer enhancement and does NOT modify core triage, routing, or booking logic. The objective is to enable hands-free symptom reporting while maintaining safety-first constraints.

---

## 2. Architectural Positioning

Voice exists in the Modality Layer only. Core logic remains text-based.

```
User Speech
    ↓
Speech-to-Text (STT)
    ↓
Core Multi-Agent Logic (unchanged)
    ↓
Text Response
    ↓
Text-to-Speech (TTS) (Optional)
```

Voice never bypasses structured intake enforcement.

---

## 3. Three-Tier Voice Architecture

| Feature | Tier 1: Browser Native | Tier 2: Whisper + TTS | Tier 3: Realtime API |
|---------|----------------------|----------------------|---------------------|
| **Technology** | Web Speech API | OpenAI Whisper (STT) + TTS | OpenAI Realtime API |
| **Cost** | Free | ~$0.02/session | ~$0.50-1.00/session |
| **Latency** | ~100ms (client-side) | ~1-2s (API round-trip) | <500ms (WebSocket) |
| **Quality** | Varies by browser | High (Whisper) | Highest (native) |
| **Interruption** | Manual (click to stop) | Manual | Native (natural) |
| **Browser** | Chrome/Edge best | All browsers | All browsers |
| **Feel** | Walkie-talkie | Walkie-talkie | Natural phone call |
| **Implementation** | ~2 hours | ~4 hours | ~8 hours |
| **API Key** | No | Yes (OpenAI) | Yes (OpenAI) |

**Recommendation:** Tier 1 for development, Tier 2 for demo, Tier 3 as stretch goal.

### Multilingual Voice Support

Voice works in all 7 supported languages:

| Language | Code | Whisper | Browser STT | GPT TTS |
|----------|------|---------|------------|---------|
| English | `en` | Yes | Yes | Yes |
| French | `fr` | Yes | Yes | Yes |
| Chinese | `zh` | Yes | Chrome | Yes |
| Arabic | `ar` | Yes | Partial | Yes |
| Spanish | `es` | Yes | Yes | Yes |
| Hindi | `hi` | Yes | Chrome | Yes |
| Urdu | `ur` | Yes | Limited | Yes |

---

## 4. Safety Requirements

Voice introduces additional clinical risk due to possible transcription errors.

### 4.1 Critical Field Confirmation

The system must confirm these fields when received via voice:

- Duration of symptoms
- Presence of red-flag symptoms (breathing difficulty, seizures, collapse)
- Species and age

Example confirmation prompt:
> "I heard that your dog has been vomiting for 2 days. Is that correct?"

### 4.2 Red-Flag Double Confirmation

If STT detects high-risk keywords:
- Ask explicit confirmation before triggering emergency escalation
- If uncertainty remains after confirmation, escalate anyway (conservative default)

### 4.3 Confidence-Based Fallback

If STT confidence score is low:
1. Request repetition of the unclear segment
2. Suggest switching to text input
3. If still unclear, route to human receptionist

Voice should never silently accept low-confidence transcriptions for safety-critical fields.

---

## 5. Failure Scenarios

| Scenario | Fallback |
|----------|----------|
| Background noise | Request repetition or text fallback |
| Multiple speakers | Ask owner to speak one at a time |
| Medical term misrecognition | Confirm with simpler phrasing |
| Pet name confusion | Confirm species and name explicitly |
| Accent variability | Whisper handles well; Web Speech API varies |
| Silence / timeout | Prompt: "Are you still there?" |

The system defaults to conservative safety decisions when voice input is ambiguous.

---

## 6. Performance Considerations

Voice adds:

- Latency (STT + TTS processing)
- Additional API costs (Tier 2/3)
- Streaming infrastructure complexity (Tier 3)
- Interrupt handling complexity (Tier 3)

Voice should not degrade core triage responsiveness.

---

## 7. Testing Requirements

| Test Category | What to Test |
|---------------|-------------|
| **Accent samples** | 3+ accent variations per language |
| **Noise levels** | Quiet, moderate, and noisy environments |
| **Red-flag phrases** | All 50+ red flags caught via voice |
| **Intent extraction** | Symptom details extracted correctly |
| **Urgency classification** | Voice-originated intakes triage correctly |
| **Fallback triggers** | Low-confidence → text fallback works |

### Metrics to Monitor

| Metric | Target |
|--------|--------|
| Word Error Rate (WER) | < 10% (Whisper), < 15% (Web Speech API) |
| Critical field extraction accuracy | ≥ 95% |
| Urgency misclassification rate | 0% for emergencies |
| Fallback trigger rate | Track (informational) |

---

## 8. When to Enable Voice

Voice is recommended when:

- Clinic receives high phone volume
- Users are frequently driving or multitasking
- Hands-free interaction improves accessibility
- Pet owners are holding a distressed pet

Voice is NOT required for core system value.

---

## 9. Architectural Principle

Voice is an enhancement layer, not a decision engine.

Core innovation remains:

- Structured intake
- Rule-grounded triage
- Safe routing
- Controlled booking

Voice should never compromise clinical safety boundaries.

---

End of Voice Extension Document
