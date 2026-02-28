

# 🐾 PetCare Agentic System

AI-powered Veterinary Triage & Smart Booking System  
A safety-first, multi-agent architecture designed to assist veterinary clinics with structured symptom intake, urgency triage, intelligent routing, and appointment booking.

---

## 🚀 Overview

PetCare Agentic System is an AI receptionist framework built to reduce call overload in veterinary clinics by:

- Collecting structured symptom information
- Safely triaging urgency levels
- Routing cases to the correct service line or veterinarian
- Booking appointments intelligently
- Generating clinic-ready structured summaries
- Providing conservative waiting guidance to pet owners

The system is designed with **layered responsibility separation**, **safety constraints**, and **extensibility** in mind.

---

## 🎯 Problem Statement

Veterinary clinics often face:

- High call volumes
- Incomplete symptom descriptions
- Mis-booked appointments
- Repeated clarification calls
- Inefficient triage consistency

This system addresses those issues through structured AI-assisted intake and routing.

---

## 🧠 System Architecture

The system follows a multi-agent orchestration model.

### 1️⃣ Modality Layer (Input/Output)

- Text Chat Interface (Primary)
- 🎤 Voice Interface (Optional Enhancement)

Voice interaction works as an I/O wrapper:

```
Voice → Speech-to-Text → Core Logic → Text Output → Text-to-Speech (Optional)
```

Voice does NOT alter business logic — it only changes interaction modality.

---

### 2️⃣ Core Multi-Agent Layer

| Agent | Responsibility |
|--------|---------------|
| Orchestrator | Controls workflow and agent sequencing |
| Intake Agent | Structures pet symptom data |
| Triage Agent | Determines urgency level (Emergency / Same-day / Soon / Routine) |
| Category Agent | Classifies symptom domain (GI / respiratory / skin / injury / behavior / chronic) |
| Routing Agent | Maps case to correct service line or doctor |
| Booking Agent | Checks availability and creates appointment |
| Safety Agent | Generates conservative waiting instructions + red-flag escalation |
| Summary Agent | Produces structured vet-facing intake summary |


---

### 3️⃣ Data Layer

Minimal MVP tables:

- `clinic_rules` – triage rules, routing mappings, safety templates
- `availability_slots` – doctor schedule & time slots
- `appointments` – booking records
- `intake_records` – structured intake logs

Agents operate under role-based data permissions to maintain safety boundaries.

---

## 🛡 Safety-First Design Principles

- No medical diagnosis generation
- Rule-grounded urgency classification
- Red-flag symptom escalation
- Structured confirmation for critical fields
- Separation between triage and booking responsibilities
- Minimal PII storage

This ensures operational safety and clinical alignment.

---

## 🎤 Voice Mode (Optional Module)

Voice interaction is designed as a modular enhancement and can be added without altering core system logic.

Possible integrations:

- Google Cloud Speech-to-Text
- OpenAI Whisper
- Web Speech API (demo only)

Voice mode requires:

- Critical symptom confirmation
- Noise-handling fallback
- Automatic downgrade to text if recognition confidence is low

For MVP demonstrations, text interaction is recommended.

---

## 🏗 Development Phases

### Phase 1 – Core Text-Based Triage (MVP)
- Structured intake
- Urgency classification
- Routing logic
- Booking simulation
- Summary generation

### Phase 2 – Production Hardening
- Database integration
- Role-based permissions
- Logging & analytics
- Red-flag testing

### Phase 3 – Voice & Telephony (Optional)
- Speech-to-text integration
- Text-to-speech responses
- Phone-based AI receptionist integration

---

## 🧪 MVP Demo Flow

1. Owner describes symptoms
2. System asks structured follow-up questions
3. Urgency level determined
4. Service line recommended
5. Available slots suggested
6. Appointment confirmed
7. Vet summary generated
8. Waiting instructions provided

---

## 🏷 Tech Stack (Suggested)

- Python / FastAPI (backend)
- LLM (OpenAI / Vertex AI)
- PostgreSQL or Firebase
- Optional: Google STT / Whisper for voice

---

## 📌 Design Philosophy

> Core innovation lies in safety-grounded triage and structured routing — not just conversational AI.

The system is built to be:

- Modular
- Extensible
- Safety-aligned
- Clinically practical

---

## 👩‍⚕️ Future Extensions

- Insurance pre-authorization agent
- Follow-up care agent
- Vaccination reminder automation
- Telemedicine integration
- Analytics dashboard for clinic operations

---

## 📄 License

Educational / Capstone Project

---

## 🤝 Contribution

This project is structured for modular expansion. Contributions should preserve:

- Safety boundaries
- Agent responsibility isolation
- Rule-grounded triage design

---

Built with safety-first agent architecture.