

# 🗄 Data Model Specification

## 1. Purpose

This document defines the minimal data model for the PetCare Agentic System.

The data model is designed to support:

- Rule-grounded triage and routing
- Scheduling and appointment booking
- Structured intake handoff to veterinary staff
- Safety-first operations with minimal PII storage

---

## 2. Data Domains (What We Store)

### 2.1 Clinic Configuration
Stores clinic-approved logic and templates used by safety-constrained agents.

- Triage rules (urgency thresholds, red flags)
- Symptom category mappings
- Routing mappings (category → service line)
- Safety guidance templates

### 2.2 Scheduling
Stores appointment availability and booking state.

- Provider schedules
- Service-line durations
- Slot availability and locking

### 2.3 Intake Records
Stores structured intake summaries for vet-facing handoff.

- Structured symptoms + answers
- Urgency and routing decisions
- Staff summary notes

### 2.4 (Optional) Profiles
Stores lightweight owner/pet profiles when the clinic supports returning patients.

- Minimal pet demographics
- Minimal owner contact
- Consent flags

---

## 3. Minimal MVP Tables

MVP is production-lean: only store what is required to run triage + booking reliably.

### 3.1 `clinic_rules`

**Goal:** Provide rule-grounded configuration for triage, routing, and safety messaging.

Suggested fields:

- `rule_id` (PK)
- `rule_type` (e.g., `TRIAGE_RED_FLAG`, `ROUTING_MAP`, `SAFETY_TEMPLATE`)
- `species` (nullable, e.g., `dog`, `cat`, `all`)
- `symptom_category` (nullable, e.g., `GI`, `RESPIRATORY`)
- `condition_key` (short key, e.g., `vomiting_blood`, `labored_breathing`)
- `severity` (e.g., `critical`, `high`, `medium`)
- `urgency_level` (nullable: `Emergency`, `Same-day`, `Soon`, `Routine`)
- `recommended_service_line` (nullable: `Urgent Care`, `General`, `Dermatology`)
- `template_text` (nullable: approved owner guidance)
- `version` (for governance)
- `is_active` (boolean)
- `effective_from` (date)
- `effective_to` (nullable date)

Notes:
- This table should be owned and approved by the clinic.
- Triage and Safety agents should **only read** from this table.

---

### 3.2 `availability_slots`

**Goal:** Represent bookable time slots by provider/service line.

Suggested fields:

- `slot_id` (PK)
- `provider_id`
- `provider_name` (optional)
- `service_line` (e.g., `General`, `Urgent Care`, `Surgery Consult`)
- `start_ts`
- `end_ts`
- `duration_minutes`
- `location_id` (optional)
- `status` (`available`, `held`, `booked`, `blocked`)
- `hold_token` (nullable)
- `hold_expires_at` (nullable)

Notes:
- Booking agent reads slots and updates `status` when holding/booking.
- For MVP, a simple lock/hold mechanism is sufficient.

---

### 3.3 `appointments`

**Goal:** Store appointment bookings and state.

Suggested fields:

- `appointment_id` (PK)
- `slot_id` (FK → `availability_slots`)
- `service_line`
- `urgency_level` (captured for audit)
- `pet_name` (optional)
- `species`
- `owner_contact` (optional; consider separate PII store)
- `status` (`confirmed`, `cancelled`, `no_show`)
- `created_at`
- `updated_at`

Notes:
- Booking agent is the only agent that writes to this table.

---

### 3.4 `intake_records`

**Goal:** Store structured intake logs and vet-facing summary.

Suggested fields:

- `intake_id` (PK)
- `appointment_id` (nullable FK)
- `created_at`
- `species`
- `age_years` (nullable)
- `weight_kg` (nullable)
- `duration_text` (e.g., `2 days`)
- `meds_text` (nullable)
- `symptoms_json` (structured key-value fields)
- `urgency_level`
- `symptom_category`
- `recommended_service_line`
- `red_flags_json` (nullable)
- `vet_summary_text`

Notes:
- Summary agent writes the `vet_summary_text`.
- Storing structured JSON reduces schema churn during iteration.

---

## 4. Optional Tables (Phase 2+)

### 4.1 `pet_profiles` (Optional)

- `pet_id` (PK)
- `owner_id` (FK)
- `pet_name`
- `species`
- `breed` (optional)
- `dob` (optional)
- `weight_kg` (optional)
- `allergies_text` (optional)
- `chronic_conditions_text` (optional)

### 4.2 `owners` (Optional)

- `owner_id` (PK)
- `full_name` (optional)
- `phone` (optional)
- `email` (optional)
- `consent_flag` (boolean)

---

## 5. Privacy & Security Guidance

### 5.1 Data Minimization
- Do not store full raw conversation transcripts in MVP.
- Prefer storing structured fields only.

### 5.2 PII Separation
- If storing contact info, isolate it in a separate table or encrypted store.

### 5.3 Role-Based Access
- Triage/Safety agents: read-only access to `clinic_rules`
- Booking agent: read/write access to scheduling + appointments
- Summary agent: write access to intake logs

### 5.4 Retention / TTL
- Intake logs and transient conversation logs should have a retention policy.

---

## 6. Example Data Flow

1. Intake agent produces structured JSON
2. Triage agent reads rules and assigns urgency
3. Routing agent reads rules and selects service line
4. Booking agent checks `availability_slots` and writes `appointments`
5. Summary agent writes `intake_records`

---

End of Data Model Document