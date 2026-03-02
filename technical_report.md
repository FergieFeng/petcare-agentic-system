# PetCare Triage & Smart Booking Agent -- Technical Report

**Authors:** Syed Ali Turab & Fergie Feng | **Team:** Broadview
**Date:** March 1, 2026

---

## Executive Summary

The PetCare Triage & Smart Booking Agent is a multi-agent proof-of-concept designed to reduce veterinary clinic front-desk workload and improve clinical routing accuracy. The system automates the pet symptom intake process through an AI-powered conversational interface, classifies urgency into four tiers (Emergency / Same-day / Soon / Routine), routes cases to the appropriate appointment type and provider pool, and generates both owner-facing guidance and a structured clinic-ready intake summary.

**Problem:** Veterinary clinic receptionists spend an average of 5 minutes per intake call asking ad-hoc symptom questions and manually determining urgency and appointment type. During peak hours, this creates queues, inconsistent triage quality, and mis-routing that leads to rescheduling and delays.

**Solution:** An orchestrator-coordinated multi-agent system that provides structured, safe, and explainable triage support -- reducing intake time while improving routing accuracy and consistency.

**Key Results:** *(to be completed after evaluation)*

---

## 1. Problem Definition

### 1.1 Who Is This For?

| User | Role | Pain Point |
|------|------|------------|
| **Clinic receptionist / intake staff** (primary) | Operational user | High call volume, inconsistent triage, manual routing |
| **Pet owners** (secondary) | Self-serve intake + scheduling | Long hold times, unclear next steps, anxiety |
| **Veterinarians / vet techs** (downstream) | Receive structured intake summary | Incomplete handoff notes, unstructured information |

### 1.2 What Is Hard Today?

- Owners call the clinic; reception staff ask ad-hoc questions, interpret urgency, choose an appointment slot, and manually explain next steps
- Intake quality varies by staff experience
- Peak-time calls create queues
- Mis-routing (wrong appointment type/doctor/urgency) leads to rescheduling and delays

### 1.3 How Often Does It Happen?

Example clinic: 30 calls/day x 5 min intake = 150 min/day spent on intake alone.

### 1.4 What Would "Better" Look Like?

- Consistent, structured intake regardless of who (or what) handles it
- Automatic red-flag detection that never misses an emergency
- Correct routing on first attempt (fewer re-bookings)
- Pet owners receive clear next steps and safe waiting guidance
- Vets get structured pre-visit summaries

---

## 2. System Architecture

### 2.1 Architecture Overview

The system uses a **7-sub-agent architecture** coordinated by a central **Orchestrator Agent**. Each sub-agent has a single responsibility and communicates via structured JSON.

```
Owner Input (symptoms, pet info)
        |
        v
+--------------------+
| A. Intake Agent    |  Collect pet profile + chief complaint + follow-ups
+--------------------+
        |
        v
+--------------------+
| B. Safety Gate     |  Detect emergency red flags
+--------------------+
        |
   [Red flag?] --Yes--> EMERGENCY ESCALATION (stop booking)
        | No
        v
+--------------------+
| C. Confidence Gate |  Verify completeness + confidence
+--------------------+
        |
   [Low confidence?] --Yes--> Ask clarifying questions (loop to Intake)
        | OK                   or route to receptionist
        v
+--------------------+
| D. Triage Agent    |  Assign urgency tier + rationale
+--------------------+
        |
        v
+--------------------+
| E. Routing Agent   |  Map symptoms → appointment type / provider
+--------------------+
        |
        v
+--------------------+
| F. Scheduling Agent|  Propose available slots / booking request
+--------------------+
        |
        v
+--------------------+
| G. Guidance &      |  Owner do/don't guidance + clinic summary
|    Summary Agent   |
+--------------------+
        |
        v
  Owner Response + Clinic-Facing Summary
```

### 2.2 Sub-Agent Responsibilities

| Agent | Input | Output | Key Logic |
|-------|-------|--------|-----------|
| **A. Intake** | Owner free-text | Structured pet profile + symptoms | Adaptive follow-ups by species + symptom area |
| **B. Safety Gate** | Structured symptoms | Red-flag boolean + escalation message | Rule-based matching against known emergencies |
| **C. Confidence Gate** | All collected fields | Confidence score + missing fields | Required-field validation + uncertainty check |
| **D. Triage** | Validated intake data | Urgency tier + rationale + confidence | Classification with evidence |
| **E. Routing** | Triage result + symptoms | Appointment type + provider pool | Clinic rule map lookup |
| **F. Scheduling** | Routing result + urgency | Available slots / booking payload | Mock calendar integration |
| **G. Guidance & Summary** | All agent outputs | Owner guidance + clinic JSON summary | Safe non-diagnostic language |

### 2.3 Autonomy Boundaries

| The agent CAN | The agent CANNOT |
|---------------|-----------------|
| Collect intake information | Give a diagnosis |
| Suggest triage urgency tier | Prescribe medications or dosing |
| Suggest appointment routing | Override clinic policy |
| Generate booking request | Finalize emergency decisions without escalation |
| Provide safe general guidance | Provide specific medical advice |
| Produce structured clinic summary | Store owner PII beyond the session |

### 2.4 Technology Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| **Backend** | Python 3.10+ / Flask | Serves API + static frontend |
| **Frontend** | Vanilla HTML / CSS / JavaScript | Chat-based intake UI |
| **LLM Provider** | OpenAI GPT-4.1 / Anthropic Claude | Configurable via `.env` |
| **Agent Framework** | Custom Python Orchestrator | POC uses in-process orchestrator (no LangGraph/ADK). Post-POC: LangGraph optional; Google ADK not recommended. |
| **Data Contracts** | JSON schemas | Structured I/O between all agents |
| **Containerization** | Docker | Single-container deployment |
| **Deployment** | Render / Railway | Free-tier cloud hosting |
| **Tracing** | LangSmith (optional) | LLM call observability |

### 2.5 Data Sources

| Source | What It Provides | Agent(s) |
|--------|-----------------|----------|
| [HuggingFace pet-health-symptoms-dataset](https://huggingface.co/datasets/karenwky/pet-health-symptoms-dataset) | 2,000 labeled symptom samples across 5 conditions (skin irritations, digestive issues, parasites, ear infections, mobility problems) | Intake (A), Triage (D) |
| [ASPCA AnTox Database](https://www.aspcapro.org/antox) | Toxin ingestion red flags from 1M+ documented poisoning cases | Safety Gate (B) |
| [ASPCA Top Toxins 2024](https://www.aspcapro.org/resource/top-10-toxins-2024) | Prioritized toxin categories (OTC meds 16.5%, food/drink 16.1%, chocolate 13.6%) | Safety Gate (B) |
| [Vet-AI Symptom Checker](https://www.vet-ai.com/symptomchecker) | 165 vet-written triage algorithms, 4M+ questions processed across 850K+ sessions | Triage (D), Routing (E) |
| [SAVSNET / PetBERT](https://github.com/SAVSNET/PetBERT) | Veterinary NLP model trained on 500M+ words from 5.1M UK vet records | Reference for NLP patterns |
| `backend/data/clinic_rules.json` | Synthetic clinic triage rules, routing maps, 4 providers, species notes | Triage (D), Routing (E) |
| `backend/data/red_flags.json` | 50+ curated emergency triggers from ASPCA + vet emergency guidelines | Safety Gate (B) |
| `backend/data/available_slots.json` | Mock clinic schedule (weekday 9-5, 30-min slots, 4 providers) | Scheduling (F) |

**Data strategy:** All POC data is synthetic or publicly available. No real patient/pet health information (PHI) is used. Future integration would connect to clinic scheduling APIs and EMR systems.

---

## 3. Design Decisions and Trade-offs

### 3.1 Key Considerations

| Consideration | Decision | Rationale |
|---------------|----------|-----------|
| **Safety vs. Convenience** | Conservative triage (escalate when uncertain) | Under-triage is far more dangerous than over-triage |
| **Latency vs. Accuracy** | Target < 15s for full intake summary | Acceptable for async intake; interactive parts are streamed |
| **Cost vs. Quality** | Route simple cases to smaller models | Only use deep reasoning for ambiguous triage |
| **Privacy** | Session-only memory, no persistent PII | Privacy-by-design; compliant with veterinary data norms |
| **Autonomy** | Never auto-send; always show human what agent decided | Clinic staff retain final authority |

### 3.2 Why an Agent (vs. Simpler Alternatives)?

A static prompt or rule-based system is insufficient because:
- The workflow is **multi-step and branching** (follow-up questions depend on symptoms and species)
- **Red-flag detection** requires both rule-based checks and contextual understanding
- **Routing logic** involves mapping symptom categories to appointment types with uncertainty handling
- The system must **escalate safely** when confidence is low or signals conflict

### 3.3 Orchestrator vs. Agent Framework (LangGraph / Google ADK)

We use a **custom Python orchestrator** rather than a formal agent framework for the POC.

| Option | Decision | Rationale |
|--------|----------|------------|
| **Custom orchestrator** | ✅ Used | Simple, debuggable, matches assignment emphasis on "simplicity and robustness" and "fewest steps." Branching (emergency, clarification) is explicit in code and in architecture diagrams. |
| **LangGraph** | Optional post-POC | Same flow; would give an explicit graph, checkpointing, and visualization (e.g. LangGraph Studio). Not required for the POC. |
| **Google ADK** | Not used | Vertex AI–centric and off our stack (OpenAI/Anthropic, Flask). Heavier than needed for this POC. |

The same 7-agent flow could be formalized in LangGraph later without changing agent logic; the report and demo can note "orchestration could be formalized in LangGraph for production" as a next step.

---

## 4. Evaluation

### 4.1 Success Metrics

| Metric | Target | Actual | Method |
|--------|--------|--------|--------|
| Triage tier agreement with clinic staff | ≥ 80% | *TBD* | Synthetic test set + manual review |
| Routing accuracy (correct appointment type) | ≥ 80% | *TBD* | Synthetic test set + manual review |
| Intake completeness (% required fields) | ≥ 90% | *TBD* | Automated field-presence check |
| Receptionist time reduction per case | 30%+ | *TBD* | Estimated from intake flow timing |
| Re-booking / mis-booking reduction | 20%+ | *TBD* | Simulated comparison |

### 4.2 Test Set

*(to be completed)*

- 20+ synthetic scenarios covering:
  - Common presentations (GI, derm, respiratory, musculoskeletal)
  - Emergency red flags (toxin ingestion, breathing difficulty, seizures, collapse)
  - Edge cases (conflicting symptoms, exotic species, vague descriptions)
  - Species variation (dog, cat, exotic)

### 4.3 Baseline Comparison

*(to be completed)*

Compare against a naive approach: keyword-matching triage without adaptive follow-ups or structured routing.

### 4.4 Strong Example

*(to be completed after evaluation)*

### 4.5 Failure Case

*(to be completed after evaluation)*

---

## 5. Risk Analysis

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Under-triage (serious case labeled routine) | **High** | Medium | Conservative red-flag rules; mandatory escalation messaging; default to "contact clinic" when uncertain |
| Over-triage (too many urgent flags) | Medium | Medium | Calibrate thresholds with scenario tests; allow receptionist override; track override rate |
| Bad routing (wrong appointment type) | Medium | Medium | Clinic-owned routing map with version control; track override reasons |
| LLM hallucination in owner guidance | **High** | Low | Strict non-diagnostic language constraints; rule-based safety gate; template-based guidance |
| Owner provides misleading info | Medium | Medium | Confidence gate + targeted follow-ups; "needs human review" flag |
| API latency exceeds target | Medium | Medium | Limit model calls via smart routing; cache static rules |

---

## 6. Feasibility and Next Steps

### 6.1 Is This Viable Beyond POC?

*(to be completed after evaluation)*

Key factors:
- Does triage accuracy meet the 80% threshold?
- Is the intake experience acceptable to pet owners?
- Can the system integrate with real clinic scheduling APIs?
- What is the cost per intake session?

### 6.2 Immediate Next Steps for Deployment Readiness

1. Integrate with a real clinic scheduling system API
2. Add persistent session logging for audit trail
3. Expand species coverage (currently focused on dogs and cats)
4. Add SMS/email notification support
5. Conduct usability testing with real clinic receptionists
6. Calibrate triage thresholds with veterinary advisor feedback
7. Add multi-language support for diverse pet owner populations

---

## Appendix

### A. Screenshots

*(to be added)*

### B. Test Set and Detailed Results

*(to be added)*

### C. Prompts Used

*(to be added -- include system prompts for each sub-agent)*

### D. Code Repository

- **Repository:** https://github.com/FergieFeng/petcare-agentic-system
- **Branch:** `PetCare_Syed`

### E. Agent Design Canvas

See the completed Agent Design Canvas submitted as a separate deliverable.
