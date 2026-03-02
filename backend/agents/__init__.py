"""
PetCare Sub-Agent Implementations

Authors: Syed Ali Turab & Fergie Feng | Team: Broadview
Date:   March 1, 2026

This package contains the 7 specialized sub-agents that form the
PetCare Triage & Smart Booking pipeline:

  A. IntakeAgent         - Adaptive symptom collection
  B. SafetyGateAgent     - Emergency red-flag detection
  C. ConfidenceGateAgent - Field validation + confidence scoring
  D. TriageAgent         - Urgency tier classification
  E. RoutingAgent        - Symptom → appointment type mapping
  F. SchedulingAgent     - Available slot proposal
  G. GuidanceSummaryAgent- Owner guidance + clinic summary generation

Each agent follows a common contract:
  Input:  Structured dict (from prior agents or session state)
  Output: Dict with keys: agent_name, status, output, confidence, warnings
"""
