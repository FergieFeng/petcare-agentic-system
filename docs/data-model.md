# Data Model Specification

**Author:** Syed Ali Turab | **Date:** March 1, 2026

---

## 1. Purpose

This document defines the data model for the PetCare Agentic System.

The model supports:

- Rule-grounded triage and routing
- Scheduling and appointment booking
- Structured intake handoff to veterinary staff
- Safety-first operations with minimal PII storage

For the **POC**, all data lives in static JSON files under `backend/data/`. The schemas below define the logical structure so that a production migration to PostgreSQL or Firebase can happen without redesigning agent logic.

---

## 2. Data Domains

### 2.1 Clinic Configuration (`clinic_rules.json`)

Stores clinic-approved logic used by safety-constrained agents.

- Triage rules: urgency thresholds, trigger keywords, actions
- Routing map: symptom category → appointment type + providers
- Provider list: names, specialties
- Species-specific notes: behavioral differences (dogs, cats, exotics)

### 2.2 Emergency Red Flags (`red_flags.json`)

A curated list of 50+ symptom phrases that trigger immediate escalation.

Categories: respiratory, bleeding, neurological, toxin ingestion, urinary, GI emergency, trauma, environmental.

### 2.3 Scheduling (`available_slots.json`)

Mock appointment availability with 30-minute slot granularity.

- Clinic hours: weekday 9-5, Saturday 9-1, Sunday closed
- 4 providers with different specialties

### 2.4 Intake Records (In-Memory)

Structured summaries generated per session. In POC, held in Python dict and returned to frontend.

### 2.5 Appointments (In-Memory)

Booking confirmations from Scheduling Agent. In POC, session memory only.

---

## 3. MVP Data Schemas

### 3.1 `clinic_rules.json`

**Read by:** Triage (D), Routing (E)  
**Written by:** None (clinic-managed)

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version |
| `clinic_name` | string | Demo clinic identifier |
| `triage_rules` | object | Keyed by urgency tier |
| `triage_rules.{tier}.description` | string | Tier description |
| `triage_rules.{tier}.triggers` | string[] | Symptom keywords |
| `triage_rules.{tier}.action` | string | Booking action |
| `routing_map` | object | Keyed by symptom category |
| `routing_map.{cat}.appointment_type` | string | Appointment type code |
| `routing_map.{cat}.providers` | string[] | Eligible providers |
| `routing_map.{cat}.notes` | string | Clinical notes |
| `providers` | array | Provider objects (name, specialties) |
| `species_notes` | object | Species-specific guidance |

### 3.2 `red_flags.json`

**Read by:** Safety Gate (B)  
**Written by:** None (curated list)

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version |
| `description` | string | File purpose |
| `red_flags` | string[] | 50+ emergency phrases for substring matching |

### 3.3 `available_slots.json`

**Read by:** Scheduling (F)  
**Written by:** Scheduling (F) in production

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version |
| `clinic_hours` | object | Hours by day type |
| `slot_duration_minutes` | integer | Default slot length (30) |
| `slots[].datetime` | string (ISO 8601) | Slot start time |
| `slots[].provider` | string | Provider name |
| `slots[].type` | string | Slot type (general, dental, surgery) |
| `slots[].available` | boolean | Whether slot is open |

### 3.4 Intake Record (In-Memory)

**Produced by:** Orchestrator  
**Consumed by:** Guidance (G), n8n webhook

| Field | Type | Description |
|-------|------|-------------|
| `intake_id` | UUID | Session identifier |
| `created_at` | ISO 8601 | Start timestamp |
| `language` | string | Session language code |
| `species` | string | Pet species |
| `chief_complaint` | string | Primary concern |
| `symptom_details` | object | Structured symptoms |
| `red_flags_detected` | string[] | Matched red flags |
| `urgency_tier` | string | Emergency / Same-day / Soon / Routine |
| `triage_rationale` | string | Urgency explanation |
| `symptom_category` | string | GI / respiratory / derm / etc. |
| `proposed_slots` | array | Slot options |
| `owner_guidance` | string | Do/don't guidance |
| `vet_summary` | object | Clinic-facing JSON |

### 3.5 Appointment (In-Memory)

**Produced by:** Scheduling (F)

| Field | Type | Description |
|-------|------|-------------|
| `appointment_id` | UUID | Appointment identifier |
| `intake_id` | FK | Link to intake |
| `slot_datetime` | ISO 8601 | Booked slot |
| `provider` | string | Assigned provider |
| `urgency_tier` | string | For audit trail |
| `status` | string | proposed / confirmed / cancelled |

---

## 4. Optional Tables (Production)

### 4.1 `pet_profiles`

| Field | Type |
|-------|------|
| `pet_id` (PK) | string |
| `owner_id` (FK) | string |
| `pet_name` | string |
| `species` | string |
| `breed` | string (nullable) |
| `weight_kg` | number (nullable) |
| `allergies` | string (nullable) |
| `chronic_conditions` | string (nullable) |

### 4.2 `owners`

| Field | Type |
|-------|------|
| `owner_id` (PK) | string |
| `full_name` | string (nullable) |
| `phone` | string (nullable) |
| `email` | string (nullable) |
| `consent_flag` | boolean |

---

## 5. Data Access Policy

| Agent | `clinic_rules` | `red_flags` | `available_slots` | Intake Records | Appointments |
|-------|:-:|:-:|:-:|:-:|:-:|
| **A — Intake** | -- | -- | -- | -- | -- |
| **B — Safety Gate** | Read | Read | -- | -- | -- |
| **C — Confidence Gate** | -- | -- | -- | -- | -- |
| **D — Triage** | Read | -- | -- | -- | -- |
| **E — Routing** | Read | -- | -- | -- | -- |
| **F — Scheduling** | -- | -- | Read | -- | Write |
| **G — Guidance** | -- | -- | -- | Write | -- |
| **Orchestrator** | Read | Read | Read | Read/Write | Read |

---

## 6. Privacy & Security

- **Data minimization:** No raw conversation transcripts stored. Voice audio transcribed and discarded.
- **PII separation:** Owner contact info not collected in POC. In production, use separate encrypted store.
- **Retention:** POC sessions lost on restart. Production: 90-day retention policy recommended.
- **Synthetic data:** All test scenarios use synthetic data. No real PHI.
- **Role-based access:** Agents have minimal privilege (see table above).

---

## 7. Data Flow Summary

```
1. Owner submits symptoms (free text or voice)
2. Intake (A) → structured pet profile + symptoms
3. Safety Gate (B) → reads red_flags.json, checks triggers
4. Confidence Gate (C) → validates fields, scores confidence
5. Triage (D) → reads clinic_rules.json, assigns urgency
6. Routing (E) → reads routing_map, selects service line
7. Scheduling (F) → reads available_slots.json, proposes slots
8. Guidance (G) → assembles owner guidance + clinic JSON
9. Orchestrator → returns to frontend + POSTs to n8n
```

---

End of Data Model Document
