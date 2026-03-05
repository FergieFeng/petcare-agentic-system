"""
PetCare Evaluation Script — M1-M4 Baseline Comparison
Runs 6 synthetic test scenarios against the live API and prints scored results.

Author: Syed Ali Turab | Team: Broadview | Date: March 4, 2026

Usage:
  python backend/evaluate.py

Requirements:
  Server must be running at http://localhost:5002
  OPENAI_API_KEY must be set in .env
"""

import requests
import json
import time
from datetime import datetime

import os as _os
BASE_URL = _os.environ.get("PETCARE_URL", "http://localhost:5002")

# Six scenarios covering emergency, routine, toxin, ambiguous, French, wellness. Gold labels for M2/M4 scoring.
TEST_CASES = [
    {
        "id": 1,
        "name": "Emergency — Respiratory Distress (Dog)",
        "messages": ["My dog is breathing fast, gums look pale, and he collapsed for a few seconds"],
        "gold_urgency": "Emergency",
        "gold_red_flag": True,
        "gold_routing": "respiratory"
    },
    {
        "id": 2,
        "name": "Routine — Skin Itching (Cat)",
        "messages": ["My cat has been scratching her neck for a week, no bleeding, still eating normally"],
        "gold_urgency": ["Soon", "Routine"],
        "gold_red_flag": False,
        "gold_routing": "dermatological"
    },
    {
        "id": 3,
        "name": "Emergency — Chocolate Toxin (Dog)",
        "messages": ["My puppy just ate a whole bar of dark chocolate about 20 minutes ago. He seems fine right now."],
        "gold_urgency": "Emergency",
        "gold_red_flag": True,
        "gold_routing": "gastrointestinal"
    },
    {
        "id": 4,
        "name": "Ambiguous — Clarification Loop",
        "messages": ["My pet is acting weird", "It's a dog", "He seems really tired and hasn't eaten in 2 days"],
        "gold_urgency": ["Same-day", "Soon"],
        "gold_red_flag": False,
        "gold_routing": None
    },
    {
        "id": 5,
        "name": "French — Vomiting Cat",
        "messages": ["Mon chat vomit depuis deux jours et ne mange plus"],
        "gold_urgency": "Same-day",
        "gold_red_flag": False,
        "gold_routing": "gastrointestinal",
        "language": "fr"
    },
    {
        "id": 6,
        "name": "Routine — Wellness Visit",
        "messages": ["I need to schedule annual vaccines for my healthy 2-year-old labrador"],
        "gold_urgency": "Routine",
        "gold_red_flag": False,
        "gold_routing": "wellness"
    },
]


def run_scenario(tc):
    """
    Run a single test scenario: start session, send messages in order, fetch summary.
    Returns dict with gold vs agent tier, red-flag match, fields_pct, elapsed_ms. (Syed Ali Turab, Mar 4, 2026)
    """
    lang = tc.get("language", "en")
    try:
        r = requests.post(f"{BASE_URL}/api/session/start", json={"language": lang}, timeout=10)
        r.raise_for_status()
        session_id = r.json()["session_id"]
    except Exception as e:
        return {"id": tc["id"], "name": tc["name"], "error": f"Session start failed: {e}"}

    start_ms = time.time() * 1000
    last_response = {}

    for msg in tc["messages"]:
        try:
            r = requests.post(
                f"{BASE_URL}/api/session/{session_id}/message",
                json={"message": msg, "language": lang},
                timeout=30
            )
            r.raise_for_status()
            last_response = r.json()
            if last_response.get("state") in ("complete", "emergency"):
                break
            time.sleep(0.5)
        except Exception as e:
            return {"id": tc["id"], "name": tc["name"], "error": f"Message failed: {e}"}

    elapsed_ms = int(time.time() * 1000 - start_ms)

    # Get evaluation_metrics from summary for M2 (tier) and M4 (red flag). (Syed Ali Turab, Mar 4, 2026)
    try:
        r = requests.get(f"{BASE_URL}/api/session/{session_id}/summary", timeout=10)
        summary = r.json()
    except Exception:
        summary = {}

    metrics   = summary.get("evaluation_metrics", {})
    agent_tier = metrics.get("triage_urgency_tier") or ""
    red_flag   = bool(metrics.get("red_flag_triggered", False))
    fields_pct = metrics.get("required_fields_captured_pct")

    gold = tc["gold_urgency"]
    tier_match = (agent_tier in gold) if isinstance(gold, list) else (agent_tier == gold)
    rf_ok      = (red_flag == tc["gold_red_flag"])

    # Return result row for summary table and JSON output.
    return {
        "id": tc["id"],
        "name": tc["name"],
        "gold_tier": gold if isinstance(gold, str) else "/".join(gold),
        "agent_tier": agent_tier or "—",
        "tier_match": tier_match,
        "gold_red_flag": tc["gold_red_flag"],
        "red_flag": red_flag,
        "red_flag_ok": rf_ok,
        "fields_pct": fields_pct,
        "elapsed_ms": elapsed_ms,
        "session_id": session_id,
    }


def main():
    """Print header, run all scenarios, print M2/M4 summary and save evaluation_results.json. (Syed Ali Turab, Mar 4, 2026)"""
    print(f"\nPetCare Evaluation — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Server: {BASE_URL}\n")

    results = []
    for tc in TEST_CASES:
        print(f"  [{tc['id']}/6] {tc['name']} ...")
        result = run_scenario(tc)
        results.append(result)

    print("\n" + "=" * 95)
    print(f"{'#':<3} {'Scenario':<44} {'Gold':<12} {'Agent':<12} {'M2':<5} {'M4':<5} {'M1 Fields%':<12} {'ms'}")
    print("=" * 95)
    for r in results:
        if "error" in r:
            print(f"{r['id']:<3} {'ERROR: ' + r['error'][:50]}")
            continue
        m2 = "✓" if r["tier_match"] else "✗"
        m4 = "✓" if r["red_flag_ok"] else "✗ MISS"
        print(f"{r['id']:<3} {r['name'][:43]:<44} {r['gold_tier']:<12} {r['agent_tier']:<12} {m2:<5} {m4:<5} {str(r['fields_pct']):<12} {r['elapsed_ms']}")

    valid    = [r for r in results if "error" not in r]
    rf_cases = [r for r in valid if r["gold_red_flag"]]
    m2_acc   = sum(1 for r in valid if r["tier_match"]) / len(valid) * 100 if valid else 0
    m4_acc   = sum(1 for r in rf_cases if r["red_flag_ok"]) / len(rf_cases) * 100 if rf_cases else 100
    avg_ms   = sum(r["elapsed_ms"] for r in valid) / len(valid) if valid else 0

    print("=" * 95)
    print(f"\nM2 Triage accuracy:     {m2_acc:.0f}%  ({sum(1 for r in valid if r['tier_match'])}/{len(valid)})  target ≥ 80%")
    print(f"M4 Red flag detection:  {m4_acc:.0f}%  ({sum(1 for r in rf_cases if r['red_flag_ok'])}/{len(rf_cases)})  target = 100%")
    print(f"Avg processing time:    {avg_ms:.0f}ms")

    _script_dir = _os.path.dirname(_os.path.abspath(__file__))
    out_path = _os.path.join(_script_dir, "evaluation_results.json")
    with open(out_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "summary": {
                "M2_triage_accuracy_pct": round(m2_acc, 1),
                "M4_red_flag_detection_pct": round(m4_acc, 1),
                "avg_processing_ms": round(avg_ms)
            }
        }, f, indent=2)
    print(f"\nFull results saved → {out_path}\n")


if __name__ == "__main__":
    main()
