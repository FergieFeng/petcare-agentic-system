# PetCare Triage & Smart Booking Agent -- Project Plan

**Authors:** Syed Ali Turab, Fergie Feng & Diana Liu | **Team:** Broadview
**Date:** March 6, 2026

**Due date:** March 22, 2026 · **Target build complete:** March 10–11, 2026 · **Current status:** Build complete, report in progress

## Overview

This project plan outlines the development of the PetCare Triage & Smart Booking Agent, a multi-agent POC for the MMAI 891 Final Project. The system automates pet symptom intake, triage urgency classification, appointment routing, and provides safe owner guidance through an orchestrator-coordinated sub-agent architecture.

---

## Phase 0: Foundation & Architecture (Week 1)

**Goal:** Establish project scaffolding, finalize architecture, and align on design decisions.

| Task | Owner | Status | Notes |
|------|-------|--------|-------|
| Clone repo and set up `main` branch | -- | Done | Branch created |
| Adapt architecture docs from main branch to PetCare domain | -- | Done | 7 sub-agents + orchestrator |
| Finalize Agent Design Canvas | -- | Done | Submitted as deliverable |
| Define I/O contracts for all sub-agents | -- | Done | JSON schemas defined in agents.md |
| Create synthetic test data (pet scenarios) | -- | Done | 6 scenarios in test_scenarios.md |
| Set up .env, requirements, project structure | -- | Done | Flask + OpenAI |

### Deliverables
- [x] Repository with `main` branch
- [x] Architecture documentation (adapted)
- [x] Agent Design Canvas (completed)
- [x] I/O contracts for all 7 sub-agents
- [x] Synthetic test dataset (v1)

---

## Phase 1: Core Agent Development (Weeks 2-3)

**Goal:** Implement the critical-path agents that form the minimum viable intake flow.

### Sprint 1 (Week 2): Intake + Safety + Triage

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Implement Intake Agent (Sub-Agent A) | -- | Done | P0 |
| Implement Safety Gate Agent (Sub-Agent B) | -- | Done | P0 |
| Implement Triage Agent (Sub-Agent D) | -- | Done | P0 |
| Create clinic rules knowledge base (`clinic_rules.json`) | -- | Done | P0 |
| Create red flags reference (`red_flags.json`) | -- | Done | P0 |
| Unit test each agent with fixture data | -- | Done (evaluate.py) | P0 |

### Sprint 2 (Week 3): Routing + Scheduling + Confidence

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Implement Confidence Gate Agent (Sub-Agent C) | -- | Done | P0 |
| Implement Routing Agent (Sub-Agent E) | -- | Done | P0 |
| Implement Scheduling Agent (Sub-Agent F) | -- | Done | P1 |
| Create mock schedule data (`available_slots.json`) | -- | Done | P1 |
| Integration test: Intake → Safety → Triage → Routing | -- | Done | P0 |

### Deliverables
- [x] 6 working sub-agents (A through F)
- [x] Clinic rules + red flags knowledge base
- [x] Mock scheduling data
- [x] Unit tests passing for each agent

---

## Phase 2: Orchestration & Summary (Week 4)

**Goal:** Wire all agents together through the orchestrator and add the guidance/summary agent.

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Implement Guidance & Summary Agent (Sub-Agent G) | -- | Done | P0 |
| Implement Orchestrator Agent | -- | Done | P0 |
| Build Flask API server (`api_server.py`) | -- | Done | P0 |
| End-to-end flow: input → all agents → output | -- | Done | P0 |
| Error handling and graceful degradation | -- | Done | P1 |
| Session memory management across agents | -- | Done | P1 |

### Deliverables
- [x] Orchestrator coordinating all 7 sub-agents
- [x] API server serving end-to-end flow
- [x] End-to-end tests passing

---

## Phase 3: Frontend & Integration (Week 5)

**Goal:** Build the user-facing chat interface and integrate with the backend.

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Build chat UI (owner-facing intake flow) | -- | Done | P0 |
| Connect frontend to Flask API | -- | Done | P0 |
| Display triage result + guidance to owner | -- | Done | P0 |
| Display clinic-facing summary (vet view) | -- | Done (JSON via webhook) | P1 |
| Add loading states, error handling in UI | -- | Done | P1 |
| Mobile-responsive design | -- | Done | P2 |

### Deliverables
- [x] Working chat-based intake UI
- [x] Integrated frontend ↔ backend
- [x] Owner-facing and clinic-facing views

---

## Phase 3.5: Voice Integration (Week 5-6)

**Goal:** Add voice input/output for hands-free intake.

### Sprint: Voice Tiers

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Implement Tier 1: Browser Web Speech API (STT + TTS) | -- | Done | P0 |
| Add mic button + TTS toggle to frontend | -- | Done | P0 |
| Implement Tier 2: OpenAI Whisper transcription endpoint | -- | Done | P1 |
| Implement Tier 2: OpenAI TTS synthesis endpoint | -- | Done | P1 |
| Test voice input across browsers (Chrome, Safari, Edge) | -- | Done (Chrome) | P1 |
| Evaluate Tier 3: OpenAI Realtime API feasibility | -- | Planned post-POC | P2 |
| Prototype Tier 3: WebSocket real-time voice (stretch goal) | -- | Planned post-POC | P2 |

### Deliverables
- [x] Voice input working (Tier 1 at minimum)
- [x] TTS response playback
- [x] Voice works alongside text input (user can switch)
- [x] Tier 2 endpoints functional (if OPENAI_API_KEY configured)

---

## Phase 4: Webhook Automation -- Actions Layer (Week 6)

**Goal:** Add post-intake webhook automation so the system can fire downstream actions (Slack, email, etc.) after the agent pipeline completes.

### Architecture

```
PetCare Agent Pipeline → Intake Complete → POST to webhook URL (if configured) → Downstream actions
```

The backend sends a JSON payload to a configurable webhook URL. The webhook receiver (n8n, Slack, Zapier, custom endpoint) handles everything after that.

### Implementation Tasks

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Add webhook POST to `api_server.py` (non-blocking) | -- | Done | P0 |
| Guard webhook behind `N8N_WEBHOOK_URL` env var | -- | Done | P0 |
| Test webhook fires on intake_complete and emergency events | -- | Done | P0 |
| Document webhook setup in DEPLOYMENT_GUIDE.md | -- | Done | P1 |

### POC Status

Webhook code is **implemented and optional**. The app runs fully without any webhook configured. For production, the webhook layer would be expanded to support multiple event types and receivers.

### Deliverables
- [x] Webhook integration implemented in PetCare backend
- [x] Fires only if `N8N_WEBHOOK_URL` is set (optional for POC)

---

## Phase 5: Evaluation & Testing (Week 7)

**Goal:** Evaluate against success metrics using the synthetic test set.

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Prepare final test set (20+ scenarios) | -- | Done (6 scenarios; expand post-POC) | P0 |
| Evaluate triage tier agreement (target ≥ 80%) | -- | Done (100% — 6/6) | P0 |
| Evaluate routing accuracy (target ≥ 80%) | -- | TBD | P0 |
| Evaluate intake completeness (target ≥ 90%) | -- | Done (100% — 5/6, scenario 1 emergency path) | P0 |
| Document strong example + failure case | -- | Done (in technical_report.md) | P0 |
| Measure latency per intake session | -- | Done (~11.4s avg) | P1 |
| Receptionist time-savings estimation | -- | Done (~96% reduction) | P1 |

### Deliverables
- [x] Evaluation results table
- [x] At least 1 strong example documented
- [x] At least 1 failure case documented with learnings
- [x] Metrics summary for report

---

## Phase 6: Consumer-Ready Features (Week 8)

**Goal:** Add consumer-ready features that make the app feel like a real product.

**Includes:** Streaming responses, consent & privacy banner, cost estimator, feedback rating, follow-up reminders, breed-specific risk alerts, dark mode, PWA support, chat transcript export, animated onboarding.

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Implement streaming text responses | -- | Done | P0 |
| Add consent & privacy banner (PIPEDA/PHIPA style) | -- | Done | P0 |
| Add cost estimator post-triage | -- | Done | P1 |
| Add feedback rating (1-5 stars) | -- | Done | P1 |
| Add follow-up reminder notifications | -- | Done | P1 |
| Add breed-specific risk alerts | -- | Done | P2 |
| Add dark mode toggle | -- | Done | P2 |
| Add PWA support (manifest, service worker) | -- | Done | P2 |
| Add chat transcript export | -- | Done | P2 |
| Add animated onboarding walkthrough | -- | Done | P2 |

### Deliverables
- [x] Streaming responses implemented
- [x] Consent banner implemented
- [x] Cost estimator implemented
- [x] Feedback rating implemented
- [x] Follow-up reminders implemented
- [x] Breed risk alerts implemented
- [x] Dark mode implemented
- [x] PWA support implemented
- [x] Chat transcript export implemented
- [x] Animated onboarding implemented

---

## Phase 7: Frontend Redesign (Week 8)

**Goal:** Transform the UI into a professional, warm PetCare-themed design.

**Design changes:** Warm teal/emerald color palette, gradient header with branded paw logo, assistant messages with paw avatars, circular send button with SVG arrow, subtle dot-pattern chat background, Inter font from Google Fonts, consistent card styling, warm dark mode.

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Redesign CSS with warm teal palette | -- | Done | P0 |
| Update header with gradient and paw branding | -- | Done | P0 |
| Add paw avatar to assistant messages | -- | Done | P0 |
| Replace text send button with circular arrow icon | -- | Done | P1 |
| Add subtle chat background pattern | -- | Done | P1 |
| Add Inter font from Google Fonts | -- | Done | P1 |
| Update dark mode with warm tones | -- | Done | P2 |
| Ensure RTL support preserved | -- | Done | P2 |

### Deliverables
- [x] Warm teal color palette applied
- [x] Gradient header with paw branding
- [x] Assistant messages with paw avatars
- [x] Circular send button with SVG icon
- [x] Chat background pattern added
- [x] Inter font integrated
- [x] Warm dark mode implemented
- [x] Responsive and RTL verified

---

## Phase 8: Report, Video & Final Polish (Week 9)

**Goal:** Complete all assignment deliverables.

**After team testing:** Report writing and demo recording. Record the POC demo video from the **Render deployment** (live URL) so the video shows the real deployed app; complete the technical report using test results and add the Render URL to the README.

| Task | Owner | Status | Priority |
|------|-------|--------|----------|
| Write technical report (`technical_report.md`) | -- | In Progress | P0 |
| Record POC demo video (10-15 min) | -- | Not Started | P0 |
| Deploy to **Render** (recommended) / Railway | -- | Done (Render-ready; Dockerfile tested) | P1 |
| Docker containerization + start scripts | -- | Done | P1 |
| Final README polish | -- | Done | P1 |
| Code cleanup and documentation | -- | Done | P2 |
| Update all docs to match current build | -- | In Progress | P1 |

### Deliverables
- [ ] Technical report (complete)
- [ ] Demo video (10-15 minutes)
- [x] Live deployment (Render-ready)
- [x] Final codebase on `main` branch
- [x] All documentation updated

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
| Webhook automation (optional actions layer) | Configurable webhook POST; handles post-intake actions without coupling to agent logic. n8n, Slack, Zapier, or custom endpoint. Optional for POC. | -- |
| Docker single-container deployment | Single Dockerfile for petcare-agent; deployed on Render | -- |
| Conservative triage defaults | Safety-first: when uncertain, escalate rather than under-triage | -- |
| Warm teal PetCare theme | Professional veterinary branding; distinct from generic blue tech products | March 6, 2026 |
| Consumer-ready features (Phase 6) | Streaming, PWA, feedback, reminders — makes the POC feel like a real product | March 6, 2026 |

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
