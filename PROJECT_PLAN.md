# PetCare Triage & Smart Booking Agent -- Project Plan

**Authors:** Syed Ali Turab & Fergie Feng | **Team:** Broadview
**Date:** March 1, 2026

**Due date:** March 22, 2026 · **Target build complete:** March 10–11, 2026

## Overview

This project plan outlines the development of the PetCare Triage & Smart Booking Agent, a multi-agent POC for the MMAI 891 Final Project. The system automates pet symptom intake, triage urgency classification, appointment routing, and provides safe owner guidance through an orchestrator-coordinated sub-agent architecture.

---

## Phase 0: Foundation & Architecture (Week 1)

**Goal:** Establish project scaffolding, finalize architecture, and align on design decisions.

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| Clone repo and create `PetCare_Syed` branch | -- | Done | Branch created from `main` |
| Adapt architecture docs from main branch to PetCare domain | -- | Done | 7 sub-agents + orchestrator |
| Finalize Agent Design Canvas | -- | Done | Submitted as deliverable |
| Define I/O contracts for all sub-agents | -- | In Progress | JSON schemas |
| Create synthetic test data (pet scenarios) | -- | Not Started | 15-20 cases covering common + urgent |
| Set up .env, requirements, project structure | -- | Done | Flask + OpenAI/Anthropic |

### Deliverables
- [x] Repository with PetCare_Syed branch
- [x] Architecture documentation (adapted)
- [x] Agent Design Canvas (completed)
- [ ] I/O contracts for all 7 sub-agents
- [ ] Synthetic test dataset (v1)

---

## Phase 1: Core Agent Development (Weeks 2-3)

**Goal:** Implement the critical-path agents that form the minimum viable intake flow.

### Sprint 1 (Week 2): Intake + Safety + Triage

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Implement Intake Agent (Sub-Agent A) | -- | Not Started | P0 |
| Implement Safety Gate Agent (Sub-Agent B) | -- | Not Started | P0 |
| Implement Triage Agent (Sub-Agent D) | -- | Not Started | P0 |
| Create clinic rules knowledge base (`clinic_rules.json`) | -- | Not Started | P0 |
| Create red flags reference (`red_flags.json`) | -- | Not Started | P0 |
| Unit test each agent with fixture data | -- | Not Started | P0 |

### Sprint 2 (Week 3): Routing + Scheduling + Confidence

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Implement Confidence Gate Agent (Sub-Agent C) | -- | Not Started | P0 |
| Implement Routing Agent (Sub-Agent E) | -- | Not Started | P0 |
| Implement Scheduling Agent (Sub-Agent F) | -- | Not Started | P1 |
| Create mock schedule data (`available_slots.json`) | -- | Not Started | P1 |
| Integration test: Intake → Safety → Triage → Routing | -- | Not Started | P0 |

### Deliverables
- [ ] 6 working sub-agents (A through F)
- [ ] Clinic rules + red flags knowledge base
- [ ] Mock scheduling data
- [ ] Unit tests passing for each agent

---

## Phase 2: Orchestration & Summary (Week 4)

**Goal:** Wire all agents together through the orchestrator and add the guidance/summary agent.

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Implement Guidance & Summary Agent (Sub-Agent G) | -- | Not Started | P0 |
| Implement Orchestrator Agent | -- | Not Started | P0 |
| Build Flask API server (`api_server.py`) | -- | Not Started | P0 |
| End-to-end flow: input → all agents → output | -- | Not Started | P0 |
| Error handling and graceful degradation | -- | Not Started | P1 |
| Session memory management across agents | -- | Not Started | P1 |

### Deliverables
- [ ] Orchestrator coordinating all 7 sub-agents
- [ ] API server serving end-to-end flow
- [ ] End-to-end tests passing

---

## Phase 3: Frontend & Integration (Week 5)

**Goal:** Build the user-facing chat interface and integrate with the backend.

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Build chat UI (owner-facing intake flow) | -- | Not Started | P0 |
| Connect frontend to Flask API | -- | Not Started | P0 |
| Display triage result + guidance to owner | -- | Not Started | P0 |
| Display clinic-facing summary (vet view) | -- | Not Started | P1 |
| Add loading states, error handling in UI | -- | Not Started | P1 |
| Mobile-responsive design | -- | Not Started | P2 |

### Deliverables
- [ ] Working chat-based intake UI
- [ ] Integrated frontend ↔ backend
- [ ] Owner-facing and clinic-facing views

---

## Phase 3.5: Voice Integration (Week 5-6)

**Goal:** Add voice input/output for hands-free intake.

### Sprint: Voice Tiers

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Implement Tier 1: Browser Web Speech API (STT + TTS) | -- | Not Started | P0 |
| Add mic button + TTS toggle to frontend | -- | Not Started | P0 |
| Implement Tier 2: OpenAI Whisper transcription endpoint | -- | Not Started | P1 |
| Implement Tier 2: OpenAI TTS synthesis endpoint | -- | Not Started | P1 |
| Test voice input across browsers (Chrome, Safari, Edge) | -- | Not Started | P1 |
| Evaluate Tier 3: OpenAI Realtime API feasibility | -- | Not Started | P2 |
| Prototype Tier 3: WebSocket real-time voice (stretch goal) | -- | Not Started | P2 |

### Deliverables
- [ ] Voice input working (Tier 1 at minimum)
- [ ] TTS response playback
- [ ] Voice works alongside text input (user can switch)
- [ ] Tier 2 endpoints functional (if OPENAI_API_KEY configured)

---

## Phase 4: n8n Workflow Automation -- Actions Layer (Week 6)

**Goal:** Add real-world automated actions that fire after the agent pipeline completes. This turns the POC from "chat interface" into "system that does things."

### Why n8n?

n8n is an open-source workflow automation platform (self-hostable via Docker, or free cloud tier). It receives webhook events from the PetCare backend and triggers downstream actions -- email, Slack, Google Sheets, etc. -- with zero code changes to the agent logic.

### Architecture

```
PetCare Agent Pipeline → Intake Complete → POST webhook to n8n → n8n Workflows
```

The backend sends a JSON payload to an n8n webhook at key events. n8n handles everything after that.

### n8n Workflows to Build

| # | Workflow | Trigger Event | Actions | Priority |
|---|----------|--------------|---------|----------|
| 1 | **Emergency Alert** | Safety Gate detects red flag | → Slack message to #emergency channel → Email on-call vet with pet profile + symptoms | P0 |
| 2 | **Clinic Summary Delivery** | Intake session completes | → Format structured summary → Email to clinic inbox → Append row to Google Sheet (intake log) | P0 |
| 3 | **Appointment Confirmation** | Scheduling Agent proposes slot | → Email pet owner with appointment details → Add event to Google Calendar (mock) | P1 |
| 4 | **Intake Analytics Logger** | Every completed session | → Log session data to Google Sheet (triage tier, confidence, latency, language used) → Use for evaluation metrics | P1 |
| 5 | **Follow-Up Reminder** | 24 hours after routine triage | → Email pet owner with follow-up guidance → Link to re-start intake if symptoms worsen | P2 |

### Implementation Tasks

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Set up n8n (Docker container or n8n Cloud free tier) | -- | Not Started | P0 |
| Create `docker-compose.yml` for petcare + n8n multi-container | -- | Not Started | P0 |
| Add webhook trigger endpoints to `api_server.py` | -- | Not Started | P0 |
| Build Workflow 1: Emergency Alert (Slack + email) | -- | Not Started | P0 |
| Build Workflow 2: Clinic Summary Delivery (email + Google Sheets) | -- | Not Started | P0 |
| Build Workflow 3: Appointment Confirmation (email) | -- | Not Started | P1 |
| Build Workflow 4: Intake Analytics Logger (Google Sheets) | -- | Not Started | P1 |
| Build Workflow 5: Follow-Up Reminder (email -- stretch) | -- | Not Started | P2 |
| Test full end-to-end: intake → agents → n8n → actions | -- | Not Started | P0 |
| Document n8n setup in DEPLOYMENT_GUIDE.md | -- | Not Started | P1 |

### n8n Deployment Options

| Option | Cost | Setup Time | Best For |
|--------|------|-----------|----------|
| **n8n Cloud (free tier)** | $0/mo (300 executions) | 5 minutes | Quick demo, no Docker needed |
| **Self-hosted (Docker)** | $0 | 15 minutes | Full control, runs alongside petcare-agent |
| **Self-hosted (docker-compose)** | $0 | 15 minutes | One-command setup for both services |

### Deliverables
- [ ] n8n running (cloud or self-hosted)
- [ ] At least 2 workflows functional (Emergency Alert + Clinic Summary)
- [ ] Webhook integration from PetCare backend
- [ ] Google Sheet with intake session log (for evaluation data)
- [ ] Docker-compose for one-command multi-container startup

---

## Phase 5: Evaluation & Testing (Week 7)

**Goal:** Evaluate against success metrics using the synthetic test set.

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Prepare final test set (20+ scenarios) | -- | Not Started | P0 |
| Evaluate triage tier agreement (target ≥ 80%) | -- | Not Started | P0 |
| Evaluate routing accuracy (target ≥ 80%) | -- | Not Started | P0 |
| Evaluate intake completeness (target ≥ 90%) | -- | Not Started | P0 |
| Document strong example + failure case | -- | Not Started | P0 |
| Measure latency per intake session | -- | Not Started | P1 |
| Receptionist time-savings estimation | -- | Not Started | P1 |
| Pull n8n analytics data from Google Sheets for evaluation | -- | Not Started | P1 |

### Deliverables
- [ ] Evaluation results table
- [ ] At least 1 strong example documented
- [ ] At least 1 failure case documented with learnings
- [ ] Metrics summary for report
- [ ] n8n session log data for evaluation

---

## Phase 6: Report, Video & Polish (Week 8)

**Goal:** Complete all assignment deliverables.

**After team testing:** Report writing and demo recording. Record the POC demo video from the **Render deployment** (live URL) so the video shows the real deployed app; complete the technical report using test results and add the Render URL to the README.

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Write technical report (`technical_report.md`) | -- | Not Started | P0 |
| Record POC demo video (10-15 min) | -- | Not Started | P0 |
| Deploy to **Render** (recommended) / Railway | -- | Not Started | P1 |
| Docker containerization + start scripts | -- | Not Started | P1 |
| Demo n8n workflows in video (show email/Slack firing) | -- | Not Started | P1 |
| Final README polish | -- | Not Started | P1 |
| Code cleanup and documentation | -- | Not Started | P2 |

### Deliverables
- [ ] Technical report (complete)
- [ ] Demo video (10-15 minutes) including n8n actions demo
- [ ] Live deployment
- [ ] Final codebase on `PetCare_Syed` branch

---

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Under-triage (serious case labeled routine) | High | Medium | Conservative red-flag rules + mandatory escalation messaging |
| Over-triage (too many cases flagged urgent) | Medium | Medium | Calibrate thresholds using scenario tests; allow receptionist override |
| Bad routing (wrong appointment type) | Medium | Medium | Maintain clinic-owned routing map + version control |
| LLM hallucination in guidance | High | Low | Strict non-diagnostic language constraints; rule-based safety gate |
| API latency exceeds 15s target | Medium | Medium | Limit model calls via routing; cache clinic rules |
| Incomplete intake (owner abandons flow) | Medium | High | Keep intake concise; show progress; allow partial submission |

---

## Key Decisions Log

| Decision | Rationale | Date |
|----------|-----------|------|
| 7-sub-agent + orchestrator architecture | Matches canvas design; enables modular testing and clear safety boundaries | -- |
| Custom orchestrator (no framework for POC) | Simplicity and robustness; assignment values "fewest steps." LangGraph optional post-POC for explicit graph; Google ADK not used (Vertex-centric, off our stack). | -- |
| Session-only memory (no persistent PII) | Privacy-by-design; no need for cross-session data in POC | -- |
| Synthetic data for all testing | No real PHI needed; enables rapid iteration and shareable test sets | -- |
| Flask backend + vanilla JS frontend | Lightweight, fast to develop, consistent with MMAI 891 project patterns | -- |
| n8n for workflow automation (actions layer) | Open-source, self-hostable, zero-code workflow builder; handles post-intake actions (email, Slack, Sheets) without coupling to agent logic | -- |
| docker-compose for multi-container setup | Runs petcare-agent + n8n side-by-side; one-command startup | -- |
| Conservative triage defaults | Safety-first: when uncertain, escalate rather than under-triage | -- |

---

## Assignment Deliverables Checklist

- [ ] Completed Agent Design Canvas
- [ ] POC Demo Video (10-15 minutes)
  - [ ] Problem definition and value proposition
  - [ ] Live demo with realistic scenarios
  - [ ] Results and learning (strong example + failure)
- [ ] Report + Appendix
  - [ ] Executive summary
  - [ ] End-to-end description
  - [ ] Key results
  - [ ] Trade-offs discussion (latency vs accuracy, safety vs convenience)
  - [ ] Risk analysis and mitigation
  - [ ] Viability beyond POC
  - [ ] Technical appendix (screenshots, test sets, code, prompts)
