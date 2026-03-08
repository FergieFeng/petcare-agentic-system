"""
Sub-Agent F: Scheduling Agent

Authors: Syed Ali Turab, Fergie Feng & Diana Liu | Team: Broadview
Date:   March 1, 2026

Proposes available appointment slots based on urgency tier,
appointment type, and provider pool. Uses mock schedule data for POC.

The scheduling agent matches the triage urgency and routing result
against the clinic's available time slots:
  - Emergency → no booking (direct to ER); returns not_applicable
  - Same-day  → filter for today's remaining slots
  - Soon      → filter for next 1-3 days
  - Routine   → any available slot in the next 7 days

Returns the top 2-3 matching slots for the owner to choose from.
If no matching slots exist, generates a manual booking request
payload that can be sent to clinic staff.

For the POC, schedule data comes from backend/data/available_slots.json.
In production, this would integrate with a real clinic scheduling API
(e.g., via REST/FHIR interface).

Input:  Routing result (appointment type + providers) + triage result (urgency)
Output: Proposed slots array or booking request payload
"""

import json
import os
import logging
from datetime import datetime, timedelta, date

logger = logging.getLogger('petcare.agents.scheduling')


class SchedulingAgent:
    """
    Appointment slot proposal agent.

    Queries available slots (mock data or API) and filters them
    based on urgency tier, appointment type, and provider pool
    from upstream agents.

    Returns a list of proposed slots for the owner to choose from,
    or a manual booking request if no matching slots are found.
    """

    def __init__(self, slots_path: str = None):
        """
        Initialize the Scheduling Agent with available slot data.

        Args:
            slots_path: Optional path to available_slots.json.
                        If not provided, generates mock slots dynamically per request.
        """
        self.agent_name = 'scheduling'
        self.slots_path = slots_path  # defer slot generation to process() so dates stay fresh

    def _load_slots(self, path: str = None) -> list:
        """
        Load available slots from a JSON file or generate mock data.

        The JSON file should have the format:
          { "slots": [
            { "datetime": "2026-03-03T09:00:00", "provider": "Dr. Chen",
              "type": "general", "available": true }, ...
          ] }

        Args:
            path: File path to available_slots.json.

        Returns:
            List of slot dicts with datetime, provider, type, available.
        """
        if path and os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f).get('slots', [])
        return self._generate_mock_slots()

    def _generate_mock_slots(self) -> list:
        """
        Generate mock available slots for the next 7 weekdays.

        Creates slots every hour from 9 AM to 4 PM for each of
        four mock providers. Skips weekends. This provides realistic
        test data without needing a real scheduling system.

        Returns:
            List of slot dicts (roughly 140 slots for a week).
        """
        slots = []
        base = datetime.now().replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        providers = ['Dr. Chen', 'Dr. Patel', 'Dr. Kim', 'Dr. Wilson']

        for day_offset in range(7):
            day = base + timedelta(days=day_offset)

            # Skip weekends (Saturday=5, Sunday=6)
            if day.weekday() >= 5:
                continue

            # Create hourly slots from 9 AM to 4 PM
            for hour in [9, 10, 11, 13, 14, 15, 16]:
                slot_time = day.replace(hour=hour, minute=0)
                for provider in providers:
                    slots.append({
                        'datetime': slot_time.isoformat(),
                        'provider': provider,
                        'type': 'general',
                        'available': True
                    })

        return slots

    def process(self, routing_result: dict, triage_result: dict) -> dict:
        """
        Find matching available slots based on routing and urgency.

        Filters the available slot pool by:
          1. Provider must be in the routing agent's provider_pool
          2. Slot must be marked as available
          3. Slot falls within the urgency date-window:
             - Same-day  → remaining slots today (after current time)
             - Soon      → next 1–3 calendar days
             - Routine   → next 7 days (full mock pool)
          4. Falls back to next-available if strict window yields no results

        Special case: Emergency tier returns no slots (direct to ER).

        Args:
            routing_result: Dict from Routing Agent with appointment_type
                            and provider_pool.
            triage_result: Dict from Triage Agent with urgency_tier.

        Returns:
            dict with standard agent output contract:
              - agent_name (str): 'scheduling'
              - status (str): 'success'
              - output (dict): proposed_slots, booking_status,
                booking_request, note (for emergencies)
              - confidence (float): 0.9 if slots found, 0.5 if not
              - warnings (list): Warning if no matching slots
        """
        # Regenerate slots fresh on every request so dates are always relative to now.
        available_slots = self._load_slots(self.slots_path)

        urgency = (
            triage_result
            .get('output', {})
            .get('urgency_tier', 'Routine')
        )
        providers = (
            routing_result
            .get('output', {})
            .get('provider_pool', [])
        )

        # EMERGENCY: Don't book — direct to emergency clinic
        if urgency == 'Emergency':
            logger.info("Emergency — skipping scheduling, direct to ER")
            return {
                'agent_name': self.agent_name,
                'status': 'success',
                'output': {
                    'proposed_slots': [],
                    'booking_status': 'not_applicable',
                    'booking_request': None,
                    'note': 'Emergency — direct to emergency clinic.'
                },
                'confidence': 1.0,
                'warnings': []
            }

        # ---------------------------------------------------------------------------
        # Urgency date-window filter
        # ---------------------------------------------------------------------------
        # Restrict the slot window based on clinical urgency so the proposed
        # times are actually appropriate:
        #   Same-day  → only slots remaining TODAY (after current time)
        #   Soon      → slots in the next 1–3 calendar days
        #   Routine   → any slot in the next 7 weekdays (the full mock pool)
        # Emergency is already handled above (no booking).
        # ---------------------------------------------------------------------------
        now = datetime.now()

        URGENCY_WINDOWS = {
            'Same-day': (now, now.replace(hour=23, minute=59, second=59)),
            'Soon':     (now + timedelta(hours=1),
                         now + timedelta(days=3, hours=23, minutes=59)),
            'Routine':  (now, now + timedelta(days=7)),
        }
        window_start, window_end = URGENCY_WINDOWS.get(urgency, URGENCY_WINDOWS['Routine'])

        def _within_window(slot: dict) -> bool:
            """Return True if the slot datetime falls within the urgency window."""
            try:
                slot_dt = datetime.fromisoformat(slot['datetime'])
                return window_start <= slot_dt <= window_end
            except (KeyError, ValueError):
                return False  # malformed slot — exclude rather than crash

        # Filter slots: available + correct provider + within urgency window
        matching_slots = [
            s for s in available_slots
            if s.get('available')
            and s.get('provider') in providers
            and _within_window(s)
        ]

        logger.info(
            f"Scheduling urgency='{urgency}' window [{window_start.strftime('%Y-%m-%d %H:%M')} "
            f"→ {window_end.strftime('%Y-%m-%d %H:%M')}]: "
            f"{len(matching_slots)} matching slots"
        )

        # If the strict window returns nothing (e.g. Same-day after 5pm),
        # fall back to the next 3 available slots regardless of window so
        # the pipeline can still produce a result rather than forcing a
        # manual booking request in all edge cases.
        if not matching_slots:
            logger.warning(
                f"No slots within urgency window for '{urgency}' — "
                "falling back to next available slots."
            )
            matching_slots = [
                s for s in available_slots
                if s.get('available') and s.get('provider') in providers
            ]

        # Take the top 3 matching slots
        proposed = matching_slots[:3]

        logger.info(
            f"Scheduling: found {len(matching_slots)} matching slots, "
            f"proposing {len(proposed)}"
        )

        return {
            'agent_name': self.agent_name,
            'status': 'success',
            'output': {
                'proposed_slots': [
                    {
                        'datetime': s['datetime'],
                        'provider': s['provider']
                    }
                    for s in proposed
                ],
                'booking_status': (
                    'proposed' if proposed else 'manual_request'
                ),
                'booking_request': (
                    None if proposed else {
                        'urgency': urgency,
                        'appointment_type': (
                            routing_result
                            .get('output', {})
                            .get('appointment_type')
                        ),
                        'note': (
                            'No matching slots found for criteria. '
                            'Please review manually.'
                        )
                    }
                )
            },
            'confidence': 0.9 if proposed else 0.5,
            'warnings': (
                [] if proposed
                else ['No matching slots found for criteria']
            )
        }
