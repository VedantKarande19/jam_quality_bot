# TVS Motor — 3-Wheeler outbound call QA rubric

**Use:** Paste this document (or its “Evaluator instructions” section) into a QA / LLM prompt with the **call transcript** (and optional audio notes). Score **every numbered criterion** from **1 to 5 stars** (1 = missing or harmful, 5 = excellent, script-aligned).

**Star anchors (apply to each criterion):**

| Stars | Meaning |
|------:|---------|
| 1 | Not done, wrong, or contradicts policy / hurts customer trust |
| 2 | Partial or weak; material gap vs script |
| 3 | Adequate; core intent met with noticeable gaps |
| 4 | Strong; minor polish only |
| 5 | Excellent; complete, natural, compliant with script intent |

**Classification:** Internal & Confidential (TVS script source material).

---

## Evaluator instructions

1. Read the full transcript (speaker labels if available: Agent / Customer).
2. Infer **call type** if possible: **first contact**, **callback**, **follow-up**, **enquiry in progress** (subtype), **not interested**, etc. Score only criteria that **apply**; for N/A items use **N/A** (do not convert N/A to a star rating).
3. For each **scored** criterion below, output: `criterion_id`, `stars` (1–5), `one_line_evidence` (quote or paraphrase from transcript), `notes` (optional).
4. End with **overall_call_quality_stars** (1–5) and **top_3_improvements** (bullets).

Suggested machine-readable block (after narrative):

```json
{
  "call_type_guess": "first_contact|callback|follow_up|enquiry_in_progress|not_interested|unknown",
  "scores": [
    {"id": "1.1", "stars": 4, "evidence": "…", "notes": "…"}
  ],
  "overall_call_quality_stars": 4,
  "top_3_improvements": ["…", "…", "…"]
}
```

---

## Reference script (TVS Motor — 3-Wheeler calling script)

### 1. Greeting & introduction

- “Good morning / afternoon / evening, this is **(CSE Name)**, calling on behalf of **TVS Motor**.”
- “Am I speaking with Mr./Ms. **[Customer Name]**?”
- If name not available: “May I know your name, please?”

### 2. Purpose of call

- “We are calling regarding your interest in **TVS 3-wheeler** vehicles.”
- “Is it a good time to speak with you?”
- **If No:** “May I know a convenient time to call back?”

**If callback**

- “Hello Mr./Ms. **[Customer Name]**, this is **(CSE Name)**, from TVS Motor.”
- “We had spoken earlier regarding your interest in TVS 3-wheeler vehicles. You had asked us to call back at a convenient time — **is now a good time to talk**?”
  - **If Yes** → Continue with main script (buying intent, features, eligibility).
  - **If No** → “May I know a better time to reach you?”

**If customer says not interested**

- “Thank you for your time. If in the future you would like to know more about TVS vehicles, we will be happy to assist.”
- “Wishing you a great day ahead!”
- *(Mark lead as Not Interested in CRM.)*

**If Yes in Q2** or **dealership change via callers** → proceed to section 3.

### 3. Customer details

- “Thank you so much!”
- “May I know which **state** you’re currently residing in?”
- “May I know your **current city**?”  
  *(If city differs from data on file → capture updated city.)*
- “May I know your **current PIN code**?”  
  *(If PIN differs from data on file → capture updated PIN.)*
- “Could you please confirm from which **dealership** you would like to purchase the vehicle?”  
  *(Confirm or capture if missing.)*  
  *(Refer to dealer list shared by TVS team and update accordingly.)*

### 4. Buying intent

- “When are you planning to buy a new 3-wheeler vehicle?”
  - **0–30 days** → **HOT LEAD** (update in HO Module)
  - **31–60 days** → **WARM LEAD**
  - **60+ days** → **COLD LEAD**

### 5. Product information / scheme information

- “Do you want to know about the product **key features** / **scheme**?” (Yes/No)
- If **Yes**, cover (as applicable): comfort, mileage, finance options, gifts under schemes such as **Surakshit Parivar ka Bharosa** & **Safar ki Guarantee**.  
  Note: Roadside assistance and warranty terms vary by model.
- **Vaada Scheme example** (e.g. TVS King EV Max): 6 years warranty; 3 free maintenance; 3 years RSA; ₹10 lakh accidental coverage; ₹1 lakh education benefit per child (up to 2 children); hospitalization up to 30 days (₹4,000/day); ₹5,000 ambulance coverage.
- If **No** → move to next step politely.

### 6. Eligibility check (only Maharashtra customers)

Confirm documents:

- a) **License** (Yes/No)  
- b) **Badge** (Yes/No)  
- c) **Permit** (Yes/No)

**Reference table (MH eligibility messaging — align explanation to model):**

| Model | Warranty | Free maintenance | RSA | Accidental | Education (₹1L/child, up to 2) | Hospitalization | Ambulance |
|------|----------|-------------------|-----|------------|----------------------------------|-----------------|-----------|
| TVS King Deluxe | 18 mo | 3 | 1 yr | 10L | 1L | ₹4,000/day up to 30 days | ₹5,000 |
| TVS King Duramax Plus | 2 yr | 3 | 1 yr | 10L | 1L | ₹4,000/day up to 30 days | ₹5,000 |
| TVS King EV Max | 6 yr | 3 | 3 yr | 10L | 1L | ₹4,000/day up to 30 days | ₹5,000 |
| TVS King Kargo HD | 3 yr | 3 | 3 yr | 10L | 1L | ₹4,000/day up to 30 days | ₹5,000 |
| TVS King Kargo HD EV | 6 yr | 3 | 3 yr | 10L | 1L | ₹4,000/day up to 30 days | ₹5,000 |

### 7. Closing

- “Thank you for your time. We will update your details and connect you with the nearest dealer for further assistance.”
- “Have a great day ahead!”

---

## Follow-up calls

- “Hello Mr./Ms. **[Customer Name]**, this is **(CSE Name)** from TVS Motor.”
- “We had spoken earlier about your interest in TVS 3-wheeler vehicles.”
- “I’m just following up to check if you had a chance to review the details we shared.”
- “Are you planning to move forward with a purchase in the next few weeks?”
  - **If Yes** → mark Hot/Warm lead by timeline.
  - **If No** → “No problem, we’ll stay in touch. May I check back with you after (X days/weeks)?”

---

## Enquiry in progress — variants

### E1. Customer will call back / will visit showroom

- Greeting + reference to earlier enquiry and dealer contact; customer had said they would call back.
- “May I know if you are currently free and interested in purchasing a 3-wheeler or would you like to visit our showroom?”
- If yes: dealer call vs showroom visit — **dispose per customer answer**.

### E2. Customer asked for home visit

- Confirm interest; offer to arrange home visit.
- “May I confirm your **preferred time and address**, so our dealer can visit you at your convenience and explain the product details in person?”
- Assurance: dealer will reach as scheduled with complete information.
- **If customer agrees** → record **time** and **address**.

### E3. Price / finance scheme already given

- Reference enquiry; dealer already shared price/finance.
- “May I know your **current willingness status** — are you interested in proceeding further with the purchase?”
- If yes: next steps (dealer call or showroom visit).

### E4. Document awaited

- Price/finance already shared; request showroom visit to submit documents.
- “May I know a **convenient time** for your visit?” — record time; follow up until visit.

### E5. Customer postponed

- Acknowledge dealer shared details; customer postponed.
- “May I know the **reason for postponing**, so we can understand your situation better and assist you accordingly?”
- Offer dealer reconnect at convenience.

**Closing (where applicable):** “Thank you for your time…” (and CRM / disposition as per process).

---

## Scoring criteria (1–5 stars each; use N/A when not applicable)

| ID | Criterion | What “5 stars” looks like |
|----|-----------|---------------------------|
| 1.1 | **Greeting & identity** | Correct TOD greeting; CSE name; TVS Motor; polite name confirmation or name capture |
| 1.2 | **Purpose & consent** | Clear purpose (3-wheeler interest); asks if good time; handles “no” with callback time |
| 1.3 | **Callback handling** | If applicable: references prior conversation; confirms convenience; reschedules politely if needed |
| 1.4 | **Not interested path** | If applicable: polite closure, no pressure, thanks + future assist + CRM intent reflected in behavior |
| 2.1 | **Customer details** | State, city, PIN; updates capture if different; dealership confirmed or captured with list discipline |
| 2.2 | **Buying intent & lead tag** | Timeline asked; HOT/WARM/COLD logic reflected in agent summary or next steps |
| 2.3 | **Product / scheme pitch** | Offers features/scheme; respects “no”; if “yes”, accurate scheme names and **Vaada** benefits without overclaiming non-listed models |
| 2.4 | **MH eligibility & documents** | Only for MH-appropriate calls: asks license/badge/permit; ties model benefits to table where relevant |
| 2.5 | **Closing** | Thanks; next step (dealer connect / update); professional sign-off |
| 3.1 | **Follow-up script** | If follow-up call: recap, review check, forward timeline, respectful persistence |
| 3.2 | **Enquiry-in-progress (E1–E5)** | If applicable subtype: correct opening, right question sequence, disposition cues (time/address/willingness/reason) |

**Overall `overall_call_quality_stars`:** holistic judgment (compliance + customer experience + completeness), still 1–5.

---

## Short LLM system prompt (optional paste)

You are a strict but fair QA scorer for TVS Motor 3-wheeler outbound calls. Use only the transcript (and any notes). Apply the rubric above. For each criterion that applies to this call, assign 1–5 stars using the anchor table. Quote brief evidence. If the call is clearly a subtype (callback, follow-up, enquiry in progress), score 3.x / follow-up items accordingly and mark unrelated items N/A. Finish with the JSON block specified in “Evaluator instructions”.
