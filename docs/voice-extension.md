
# 🎤 Voice Extension Design

## 1. Purpose

This document defines the optional Voice Interaction Module for the PetCare Agentic System.

Voice is treated strictly as an interaction-layer enhancement and does NOT modify core triage, routing, or booking logic.

The objective is to enable hands-free symptom reporting while maintaining safety-first constraints.

---

## 2. Architectural Positioning

Voice exists in the Modality Layer only.

Core logic remains text-based.

```
User Speech
    ↓
Speech-to-Text (STT)
    ↓
Core Multi-Agent Logic
    ↓
Text Response
    ↓
Text-to-Speech (TTS) (Optional)
```

Voice never bypasses structured intake enforcement.

---

## 3. Supported Modes

### Mode A — Voice Input Only (Recommended for MVP)
- User speaks
- STT converts to text
- System processes text normally
- Output shown as text

This minimizes system complexity and reduces TTS latency.

### Mode B — Full Voice Conversation (Advanced)
- User speaks
- STT converts to text
- System processes
- Response converted to speech

This requires turn-taking logic and interruption handling.

---

## 4. Suggested STT/TTS Providers

### Speech-to-Text (STT)
- Google Cloud Speech-to-Text
- OpenAI Whisper
- Browser Web Speech API (Demo Only)

### Text-to-Speech (TTS)
- Google Cloud Text-to-Speech
- Azure TTS
- ElevenLabs (optional)

Production systems should use enterprise-grade STT.

---

## 5. Safety Requirements

Voice introduces additional clinical risk due to possible transcription errors.

### 5.1 Critical Field Confirmation
The system must confirm:

- Duration of symptoms
- Presence of red-flag symptoms (e.g., breathing difficulty, seizures, collapse)
- Species and age

Example:

> “I heard that your dog has been vomiting for 2 days. Is that correct?”

### 5.2 Red-Flag Double Confirmation
If STT detects high-risk keywords:
- Ask explicit confirmation
- If uncertainty remains, escalate urgency

### 5.3 Confidence-Based Fallback
If STT confidence score is low:
- Request repetition
- Switch to text input
- Suggest direct clinic call

---

## 6. Failure Scenarios

Voice layer must handle:

- Background noise
- Multiple speakers
- Medical term misrecognition
- Pet name confusion
- Accent variability

System must default to conservative safety decisions when ambiguity exists.

---

## 7. Performance Considerations

Voice adds:

- Latency (STT + TTS)
- Additional API costs
- Streaming infrastructure complexity
- Interrupt handling complexity

Voice should not degrade core triage responsiveness.

---

## 8. Testing Requirements

Voice testing must include:

- Multiple accent samples
- Noise-level testing
- Red-flag phrase testing
- Intent extraction accuracy
- Urgency misclassification testing

Metrics to monitor:

- Word Error Rate (WER)
- Critical field extraction accuracy
- Urgency misclassification rate

---

## 9. When to Enable Voice

Voice is recommended when:

- Clinic receives high phone volume
- Users are frequently driving or multitasking
- Hands-free interaction improves accessibility

Voice is NOT required for core system value.

---

## 10. Architectural Principle

Voice is an enhancement layer, not a decision engine.

Core innovation remains:

- Structured intake
- Rule-grounded triage
- Safe routing
- Controlled booking

Voice should never compromise clinical safety boundaries.

---

End of Voice Extension Document