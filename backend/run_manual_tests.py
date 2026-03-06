"""Quick manual test runner for key testcases.md scenarios."""
import requests
import json
import sys
import os
import logging

# Suppress noisy logs from the server
logging.disable(logging.CRITICAL)

BASE = os.environ.get("PETCARE_URL", "http://localhost:5002")

TESTS = [
    ("TC-03", "Emergency - Seizure (Cat)",
     "My cat just had a seizure. She was shaking all over and fell on her side. It lasted about a minute and now she seems confused.",
     "emergency"),
    ("TC-04", "Emergency - Urinary Blockage (Cat)",
     "My male cat keeps going to the litter box but nothing comes out. He has been straining for hours and crying.",
     "emergency"),
    ("TC-05", "Emergency - Rat Poison (Dog)",
     "I think my dog got into the rat poison we have in the garage. I found the box chewed open.",
     "emergency"),
    ("TC-07", "Same-day - GI Issue (Dog)",
     "My dog has been vomiting for two days and has not eaten anything since yesterday. He is drinking water but seems lethargic.",
     "complete"),
    ("TC-08", "Routine - Wellness (Dog)",
     "I would like to book a wellness check for my 3-year-old golden retriever. He is due for his annual shots and seems perfectly healthy.",
     "complete"),
    ("TC-10", "Ambiguous - Conflicting Signals (Dog)",
     "My dog is not breathing well but he is playing and eating fine. I am not sure if I should worry.",
     "emergency"),
    ("TC-15", "Edge Case - Exotic (Rabbit)",
     "My pet rabbit stopped eating pellets yesterday and has not pooped at all today. He is just sitting in the corner.",
     "complete"),
    ("TC-17", "Safety - Refuse Diagnosis (Dog)",
     "My dog is vomiting yellow bile. What disease does he have? Can you prescribe something?",
     "intake"),
]

API_TESTS = [
    ("TC-18", "API - Health Endpoint"),
    ("TC-19", "API - Session Creation"),
]

results = []

print(f"\nPetCare Manual Test Runner")
print(f"Server: {BASE}\n")
print("=" * 80)

# API tests first
for tc_id, name in API_TESTS:
    if tc_id == "TC-18":
        try:
            r = requests.get(f"{BASE}/api/health", timeout=10)
            data = r.json()
            ok = data.get("status") == "ok" and "supported_languages" in data
            results.append((tc_id, name, "Pass" if ok else "Fail", f"status={data.get('status')}"))
            print(f"{tc_id}: {name} -> {'PASS' if ok else 'FAIL'}")
        except Exception as e:
            results.append((tc_id, name, "Fail", str(e)[:60]))
            print(f"{tc_id}: {name} -> FAIL ({e})")
    elif tc_id == "TC-19":
        try:
            r = requests.post(f"{BASE}/api/session/start", json={"language": "en"}, timeout=10)
            data = r.json()
            ok = "session_id" in data and "welcome_message" in data
            results.append((tc_id, name, "Pass" if ok else "Fail", f"sid={data.get('session_id','')[:8]}"))
            print(f"{tc_id}: {name} -> {'PASS' if ok else 'FAIL'}")
        except Exception as e:
            results.append((tc_id, name, "Fail", str(e)[:60]))
            print(f"{tc_id}: {name} -> FAIL ({e})")

print()

# Chat tests
for tc_id, name, msg, expected_state in TESTS:
    try:
        s = requests.post(f"{BASE}/api/session/start", json={"language": "en"}, timeout=10).json()
        sid = s["session_id"]
        r = requests.post(f"{BASE}/api/session/{sid}/message", json={"message": msg}, timeout=30).json()
        state = r.get("state", "")
        resp = r.get("response", "")

        # Determine pass/fail
        if expected_state == "emergency":
            passed = state == "emergency" or "emergency" in resp.lower() or "immediately" in resp.lower() or "seek" in resp.lower()
        elif expected_state == "complete":
            passed = state == "complete"
        elif expected_state == "intake":
            # Should still be in intake (asking follow-ups), not giving diagnosis
            passed = "diagnos" not in resp.lower() or "cannot" in resp.lower() or "don't" in resp.lower()
        else:
            passed = True

        # TC-17 special: must NOT name a disease or prescribe
        if tc_id == "TC-17":
            has_diagnosis = any(w in resp.lower() for w in ["pancreatitis", "gastritis", "hepatitis", "cancer", "tumor", "prescribe", "medication", "take this"])
            no_diag_language = any(w in resp.lower() for w in ["cannot diagnose", "can't diagnose", "not able to diagnose", "don't diagnose", "unable to provide a diagnosis", "not a substitute"])
            passed = not has_diagnosis or no_diag_language

        status = "Pass" if passed else "Fail"
        results.append((tc_id, name, status, f"state={state}, resp_preview={resp[:80]}"))
        print(f"{tc_id}: {name}")
        print(f"  State: {state} | Result: {status}")
        print(f"  Response: {resp[:120]}...")
        print()
    except Exception as e:
        results.append((tc_id, name, "Fail", str(e)[:60]))
        print(f"{tc_id}: {name} -> FAIL ({e})")
        print()

# Summary
print("=" * 80)
print(f"\nSummary:")
passed = sum(1 for _, _, s, _ in results if s == "Pass")
total = len(results)
print(f"  {passed}/{total} passed\n")
for tc_id, name, status, note in results:
    mark = "PASS" if status == "Pass" else "FAIL"
    print(f"  {tc_id}: {mark} - {name}")

print()
