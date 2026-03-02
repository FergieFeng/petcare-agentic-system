# Non-Technical Workflow

**Authors:** Syed Ali Turab & Fergie Feng | **Contributors:** Diana Liu | **Team:** Broadview | **Date:** March 1, 2026

This version explains the PetCare Triage & Smart Booking Agent workflow for non-technical readers.

For the technical version (flowchart + JSON contracts), see `docs/architecture/workflow_technical.md`.

---

## What the System Does

The PetCare Agent helps veterinary clinics and pet owners by answering three practical questions when a pet is unwell:

1. **How urgent is this?** (Emergency, Same-day, Soon, or Routine)
2. **What kind of appointment is needed?** (and which vet should see the pet)
3. **What should the owner do while waiting?** (safe, non-medical guidance)

---

## How It Works (Simple View)

1. The pet owner describes their pet's symptoms through a chat interface.
2. The system asks follow-up questions based on the type of symptoms (e.g., how often is the pet vomiting? is there blood?).
3. It checks for emergency warning signs (like difficulty breathing, seizures, or suspected poisoning).
   - If an emergency is detected, the owner is immediately told to go to an emergency clinic.
4. It classifies how urgent the situation is.
5. It figures out what kind of appointment is needed and which vets are available.
6. It suggests appointment times.
7. It gives the owner safe "do and don't" tips for while they wait.
8. It sends the vet a structured summary of everything collected.

---

## What the Owner Sees

- A conversational chat where they describe what's happening with their pet
- A clear urgency level (e.g., "Same-day visit recommended")
- Appointment options to choose from
- Helpful tips (e.g., "Do: keep water available. Don't: force-feed your pet.")

---

## What the Clinic Staff Sees

- A structured intake summary with:
  - Pet profile (name, species, breed, age, weight)
  - Symptom timeline and details
  - Urgency classification with reasoning
  - Suggested appointment type and available vets
  - Confidence level (so staff know when to double-check)

---

## Example (Non-Technical)

### Input
- Owner types: "My dog Bella has been vomiting since yesterday and won't eat. She got into the garbage two days ago."

### System Response
- **Urgency:** Same-day visit recommended
- **Why:** Persistent vomiting (4 times in 24 hours) with reduced appetite and possible foreign material ingestion. No emergency red flags.
- **Appointment:** Sick visit with Dr. Chen at 2:00 PM or Dr. Patel at 3:30 PM
- **While you wait:**
  - Do: keep fresh water available, monitor for worsening
  - Don't: force-feed, give human medications
  - Watch for: blood in vomit, difficulty breathing, extreme lethargy → if any of these occur, go to emergency clinic immediately

---

## What This Does NOT Do

- It does **not** diagnose your pet's condition
- It does **not** prescribe medications
- It does **not** replace a veterinary examination
- It provides **triage support and safe guidance** to help you get the right care faster

---

## Safety First

The system is designed with safety as the top priority:

- If there's any doubt, it recommends a higher urgency level (better safe than sorry)
- It always tells owners to seek emergency care if certain warning signs appear
- It never gives medical diagnoses or treatment advice
- Clinic staff can always override the system's suggestions
