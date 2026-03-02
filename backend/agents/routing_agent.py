"""
Sub-Agent E: Routing Agent

Authors: Syed Ali Turab & Fergie Feng | Team: Broadview
Date:   March 1, 2026

Maps symptom category to appointment type and provider pool
using the clinic's routing rules.

The routing agent translates the triage result and symptom data into
a concrete appointment configuration:
  1. Identifies the symptom category (GI, respiratory, derm, etc.)
  2. Looks up the clinic's routing map for that category
  3. Returns the appointment type, provider pool, and any special
     requirements (e.g., "may need imaging")

The routing map is loaded from backend/data/clinic_rules.json
or falls back to a hardcoded default map. This design allows each
clinic to customize their routing without code changes.

Routing categories:
  - gastrointestinal  → sick_visit_urgent
  - respiratory       → sick_visit_urgent
  - dermatological    → sick_visit_routine
  - injury            → sick_visit_urgent
  - urinary           → sick_visit_urgent
  - dental            → sick_visit_routine
  - behavioral        → sick_visit_routine
  - wellness          → wellness
  - other/unknown     → sick_visit_routine (safe default)

If the triage tier is Emergency, the appointment type is always
overridden to 'emergency' regardless of the routing map.

Input:  Intake data + triage result
Output: Symptom category, appointment type, provider pool, requirements
"""

import json
import os
import logging

logger = logging.getLogger('petcare.agents.routing')

# ---------------------------------------------------------------------------
# Default Routing Map
# ---------------------------------------------------------------------------
# Maps symptom categories to appointment types and provider pools.
# This is the fallback when no clinic_rules.json is provided.
# Each clinic can customize this via their own JSON config.

DEFAULT_ROUTING_MAP = {
    'gastrointestinal': {
        'appointment_type': 'sick_visit_urgent',
        'providers': ['Dr. Chen', 'Dr. Patel']
    },
    'respiratory': {
        'appointment_type': 'sick_visit_urgent',
        'providers': ['Dr. Chen', 'Dr. Kim']
    },
    'dermatological': {
        'appointment_type': 'sick_visit_routine',
        'providers': ['Dr. Patel', 'Dr. Wilson']
    },
    'injury': {
        'appointment_type': 'sick_visit_urgent',
        'providers': ['Dr. Chen', 'Dr. Kim']
    },
    'urinary': {
        'appointment_type': 'sick_visit_urgent',
        'providers': ['Dr. Patel', 'Dr. Chen']
    },
    'dental': {
        'appointment_type': 'sick_visit_routine',
        'providers': ['Dr. Wilson']
    },
    'behavioral': {
        'appointment_type': 'sick_visit_routine',
        'providers': ['Dr. Kim']
    },
    'wellness': {
        'appointment_type': 'wellness',
        'providers': ['Dr. Patel', 'Dr. Wilson', 'Dr. Kim']
    },
    'other': {
        'appointment_type': 'sick_visit_routine',
        'providers': ['Dr. Chen', 'Dr. Patel']
    }
}


class RoutingAgent:
    """
    Symptom-to-appointment routing agent.

    Uses a clinic-defined routing map to translate symptom categories
    into concrete appointment configurations. The routing map is
    loaded from a JSON config file, allowing per-clinic customization.

    Override rule: Emergency triage tier always maps to 'emergency'
    appointment type, regardless of what the routing map says.
    """

    def __init__(self, clinic_rules_path: str = None):
        """
        Initialize the Routing Agent with a clinic rules configuration.

        Args:
            clinic_rules_path: Optional path to clinic_rules.json.
                               If not provided, uses DEFAULT_ROUTING_MAP.
        """
        self.agent_name = 'routing'
        self.routing_map = self._load_routing_map(clinic_rules_path)

    def _load_routing_map(self, path: str = None) -> dict:
        """
        Load routing rules from a JSON config file.

        The JSON file should have the format:
          { "routing_map": { "gastrointestinal": { ... }, ... } }

        Args:
            path: File path to clinic_rules.json.

        Returns:
            Dict mapping symptom categories to appointment configs.
        """
        if path and os.path.exists(path):
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get('routing_map', DEFAULT_ROUTING_MAP)
        return DEFAULT_ROUTING_MAP

    def process(self, intake_data: dict, triage_result: dict) -> dict:
        """
        Map symptom category to appointment type and provider pool.

        Looks up the symptom area from the intake data in the routing
        map and returns the matching appointment configuration.
        Emergency triage tier overrides to 'emergency' appointment type.

        Args:
            intake_data: Dict from Intake Agent with symptom_details
                         (including 'area' field).
            triage_result: Dict from Triage Agent with urgency_tier.

        Returns:
            dict with standard agent output contract:
              - agent_name (str): 'routing'
              - status (str): 'success'
              - output (dict): symptom_category, appointment_type,
                provider_pool, special_requirements
              - confidence (float): 0.85 (high for rule-based lookup)
              - warnings (list): Any issues
        """
        # Get the symptom area from intake data.
        # Falls back to 'other' if not identified.
        symptom_area = (
            intake_data
            .get('symptom_details', {})
            .get('area', 'other')
        )

        # Look up the routing map for this symptom category
        route = self.routing_map.get(
            symptom_area,
            self.routing_map.get('other', DEFAULT_ROUTING_MAP['other'])
        )

        # Emergency override: if triage says Emergency, force
        # the appointment type to 'emergency' regardless of routing map
        urgency = triage_result.get('output', {}).get('urgency_tier', 'Routine')
        if urgency == 'Emergency':
            appointment_type = 'emergency'
        else:
            appointment_type = route['appointment_type']

        logger.info(
            f"Routing: {symptom_area} → {appointment_type}, "
            f"providers: {route['providers']}"
        )

        return {
            'agent_name': self.agent_name,
            'status': 'success',
            'output': {
                'symptom_category': symptom_area,
                'appointment_type': appointment_type,
                'provider_pool': route['providers'],
                'special_requirements': None
            },
            'confidence': 0.85,
            'warnings': []
        }
