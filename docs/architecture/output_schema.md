# Output Schema

**Authors:** Syed Ali Turab & Fergie Feng | **Contributors:** Diana Liu | **Team:** Broadview | **Date:** March 1, 2026

This document defines the canonical JSON output schema for the PetCare Triage & Smart Booking Agent. All system outputs must conform to this schema for consistency, evaluation, and clinic integration.

---

## Two Output Modes

The system produces two aligned outputs per intake session:

1. **Owner-Facing Response** -- natural language delivered via chat
2. **Clinic-Facing Summary** -- structured JSON for clinical staff and downstream systems

---

## Owner-Facing Response Schema

```json
{
  "urgency_level": "Same-day",
  "urgency_message": "We recommend a same-day veterinary visit for Bella.",
  "next_steps": "We've found available appointment slots for you. Please select one below.",
  "proposed_slots": [
    { "datetime": "2026-03-01T14:00:00", "provider": "Dr. Chen" },
    { "datetime": "2026-03-01T15:30:00", "provider": "Dr. Patel" }
  ],
  "guidance": {
    "do": [
      "Keep fresh water available",
      "Monitor for any worsening symptoms",
      "Note any new vomiting episodes"
    ],
    "dont": [
      "Do not force-feed your pet",
      "Do not give human medications without vet guidance",
      "Do not wait if breathing difficulty develops"
    ],
    "watch_for": [
      "Blood in vomit or stool",
      "Difficulty breathing",
      "Extreme lethargy or collapse",
      "Abdominal swelling"
    ]
  }
}
```

---

## Clinic-Facing Summary Schema

```json
{
  "version": "1.0.0",
  "session_id": "string (unique session identifier)",
  "timestamp": "ISO 8601 datetime",

  "pet_profile": {
    "name": "string",
    "species": "string (dog | cat | other)",
    "breed": "string",
    "age": "string",
    "weight": "string (with unit)"
  },

  "chief_complaint": "string (owner's primary concern)",

  "symptom_details": {
    "area": "string (gastrointestinal | respiratory | dermatological | musculoskeletal | urinary | neurological | dental | behavioral | other)",
    "specific_symptoms": "object (area-dependent fields)",
    "timeline": "string (when symptoms started)",
    "eating_drinking": "string (normal | reduced | none)",
    "energy_level": "string (normal | reduced | lethargic)"
  },

  "red_flags": {
    "detected": "boolean",
    "flags": ["array of string (detected red flag descriptions)"],
    "escalation_triggered": "boolean"
  },

  "triage": {
    "urgency_tier": "string (Emergency | Same-day | Soon | Routine)",
    "rationale": "string (evidence-based explanation)",
    "confidence": "number (0-1)",
    "contributing_factors": ["array of string"]
  },

  "routing": {
    "symptom_category": "string",
    "appointment_type": "string (emergency | sick_visit_urgent | sick_visit_routine | wellness | specialist_referral)",
    "provider_pool": ["array of string (provider names)"],
    "special_requirements": "string | null"
  },

  "scheduling": {
    "proposed_slots": ["array of ISO 8601 datetime strings"],
    "booking_status": "string (proposed | confirmed | manual_request | not_applicable)",
    "booking_request": "object | null (payload for manual booking)"
  },

  "confidence": {
    "overall": "number (0-1)",
    "intake_completeness": "number (0-1)",
    "triage_confidence": "number (0-1)",
    "needs_review": "boolean"
  },

  "owner_guidance": {
    "do": ["array of string"],
    "dont": ["array of string"],
    "watch_for": ["array of string"]
  },

  "metadata": {
    "processing_time_ms": "integer",
    "agents_executed": ["array of string"],
    "clarification_loops": "integer (0-2)",
    "model_provider": "string",
    "model_name": "string"
  }
}
```

---

## Field Requirements

### Required Fields (must always be present)

- `version`, `session_id`, `timestamp`
- `pet_profile.species`
- `chief_complaint`
- `red_flags.detected`, `red_flags.escalation_triggered`
- `triage.urgency_tier`, `triage.confidence`
- `confidence.overall`, `confidence.needs_review`
- `metadata.processing_time_ms`, `metadata.agents_executed`

### Optional Fields (present when applicable)

- `pet_profile.name`, `pet_profile.breed`, `pet_profile.age`, `pet_profile.weight`
- `symptom_details.specific_symptoms` (structure varies by symptom area)
- `routing.special_requirements`
- `scheduling.booking_request`

---

## Urgency Tier Definitions

| Tier | Definition | Target Response |
|------|-----------|----------------|
| **Emergency** | Life-threatening condition requiring immediate care | Direct to emergency clinic NOW |
| **Same-day** | Significant concern that should be seen today | Book within hours |
| **Soon** | Non-urgent but should be seen within 1-3 days | Schedule next available |
| **Routine** | Standard wellness or minor concern | Schedule at convenience |

---

## Validation Rules

1. If `red_flags.detected` is `true`, `triage.urgency_tier` must be `"Emergency"`
2. If `triage.urgency_tier` is `"Emergency"`, `scheduling.booking_status` must be `"not_applicable"` (direct to ER)
3. `confidence.overall` must be between 0 and 1
4. `metadata.agents_executed` must contain at least `["intake", "safety_gate"]`
5. If `confidence.needs_review` is `true`, the clinic summary must include a review flag
