---
title: "PayProof AI — Unique Selling Proposition Document"
document: "USP"
version: "0.1"
status: "Positioning hypothesis — must be validated"
date: "2026-09-19"
---

# PayProof AI — Unique Selling Proposition

## 1. Positioning statement

For **accounts-payable and finance teams that still verify vendor payment changes by manually reconciling email, invoices, purchase orders, vendor-master data and history**, PayProof AI is an **evidence-bound pre-payment verification workspace** that turns fragmented material into a source-linked decision dossier before funds are released.

Unlike a generic phishing classifier or an opaque fraud score, PayProof separates deterministic checks from AI interpretation, shows contradictory and missing evidence, enforces human approval boundaries, and records why a payment was cleared for normal approval, escalated or held.

## 2. Core USP

> **Evidence before decision: PayProof does not ask an AI model whether a payment "looks fraudulent." It constructs a verifiable case from the evidence the finance team already has, runs deterministic controls first, uses AI only for bounded semantic tasks, and tells the reviewer exactly what conflicts, what is missing, and what must happen before payment can proceed.**

This is the product's strongest current differentiation thesis.

It is a **combination USP**, not a claim that no competitor has any of these capabilities individually.

## 3. Five product differentiators

### USP-1 — Evidence-bound decision dossier

Every material finding must link back to a source:

```text
Finding:
NEW_BENEFICIARY_ACCOUNT

Evidence:
vendor_baseline.json -> account ****4201
invoice_88392.pdf     -> account ****7812
email_2026_09_19.eml  -> requests account ****7812

Result:
Independent vendor verification required
```

The system does not convert this into a hidden score and discard the underlying facts.

### USP-2 — Deterministic-first, AI-second

Use ordinary code for facts that ordinary code can verify:

- equality;
- duplicate detection;
- history lookup;
- amount mismatch;
- new beneficiary;
- sender-domain comparison;
- missing evidence;
- approval-state lookup.

Use Nemotron only for semantics:

- "Is this text requesting a bank change?"
- "Does this email claim somebody already approved the change?"
- "Which vendor name does this sentence refer to?"
- "Summarize the evidence conflicts without inventing facts."

This makes the product easier to test, explain and fail safely.

### USP-3 — Missing evidence is a first-class output

Most systems are tempted to output a confidence/risk number even when inputs are incomplete.

PayProof should instead say:

```text
Cannot reach standard-clearance state.

Missing:
- trusted historical beneficiary
- recorded independent verification
- matching PO

Next action:
obtain or verify the missing evidence
```

Uncertainty remains visible.

### USP-4 — Integration-light adoption wedge

The BUILD IT product can work with:

- file uploads;
- CSV exports;
- `.eml`;
- JSON/reference records.

That allows a team to evaluate the workflow before a major ERP/email/payment integration project.

This is commercially useful only if customer interviews confirm that integration effort is a real barrier.

### USP-5 — Human and policy authority are explicit

The LLM is never the approver.

The product differentiates between:

- model interpretation;
- deterministic finding;
- business decision policy;
- authorization policy;
- human disposition.

That separation is important for a finance workflow.

## 4. What is *not* unique

To avoid false positioning:

- Eftsure already emphasizes independent vendor/bank verification and continuous assurance.
- PaymentWorks already provides vendor onboarding, verification, permissions and auditable change workflows.
- Trustmi publicly describes AI-assisted vendor validation with evidence and reasoning.
- Medius already provides AP fraud/risk factors, invoice verification and approval controls.

Therefore these claims would be weak or false:

- "the first AI system to verify vendors";
- "the only system that checks bank changes";
- "the first explainable AP fraud product";
- "the only human-in-the-loop payment-security platform."

PayProof must win on **workflow design, evidence traceability, integration friction, safe AI boundaries and usability**, then build proprietary advantage from deployments/data/integrations.

## 5. Defensibility roadmap

### Stage 0 — No moat yet
At repository/MVP stage the product has an architecture and workflow thesis, not a defensible business moat.

### Stage 1 — Workflow moat
Build the best structured schema for:

- payment-change cases;
- evidence provenance;
- contradictions;
- verification actions;
- resolution outcomes.

### Stage 2 — Integration moat
Add high-value connectors selected from customer demand.

### Stage 3 — Outcome data moat
With customer consent and privacy controls, collect de-identified/tenant-isolated patterns such as:

- which findings cause escalation;
- which anomalies are benign;
- which verification steps resolve cases;
- false-positive patterns.

This must not become a cross-customer data pool without explicit legal/privacy basis.

### Stage 4 — Trust network or external data partnerships
Competitive parity with major vendors may ultimately require:

- bank-account ownership data;
- business identity data;
- sanctions/KYB;
- verified supplier channels.

This is expensive and not solved by LLM engineering.

## 6. Messaging hierarchy

### Primary message
**Verify the evidence before you trust the payment change.**

### Supporting message
**One case. Every source. Every contradiction. Every approval step.**

### Technical message
**Deterministic controls first; bounded AI reasoning second; humans retain payment authority.**

### Demo message
**Upload the invoice, email, PO and vendor history. PayProof shows what changed and what must be verified before payment proceeds.**

## 7. Candidate taglines

Use only after product naming/trademark review:

- **Evidence before payment.**
- **Verify the change, not the email.**
- **Know why a payment is being held.**
- **From fragmented evidence to an auditable payment decision.**

Avoid fear-heavy messaging such as "Stop every fraudster."

## 8. Proof required for each USP

| USP claim | Required proof |
|---|---|
| Consolidates fragmented evidence | working ingestion + unified case |
| Source-linked findings | every finding contains evidence references |
| Deterministic-first | documented rule inventory + tests |
| Bounded AI | tool allowlist + structured schemas + failure tests |
| Missing-evidence awareness | explicit rule and UI state |
| Human authority | approval permissions and audit events |
| Integration-light | complete demo from files/exports only |
| Faster review | measured user study, not developer timing |
| Reduces errors/fraud | controlled customer/benchmark evidence; not available at MVP start |

## 9. Product trust contract

The user should be able to rely on these statements:

1. The system distinguishes source facts from model inference.
2. An AI response cannot directly release a payment.
3. A missing critical check is shown as missing, not guessed.
4. A high-risk case can fail closed if configured.
5. Every state-changing human action is recorded.
6. The evidence record can be exported.
7. The product will not claim that a bank account is verified unless an external verification source actually verifies it.

## 10. "Why now" argument

The product does not need a speculative AI narrative.

The current timing case is:

- BEC/payment-fraud losses remain material;
- vendor impersonation is a documented problem;
- LLMs are capable of assisting with messy finance-language interpretation;
- structured tool calling allows AI to be constrained behind typed interfaces;
- open-source orchestration frameworks such as Strands allow local development without AWS-hosted agent infrastructure;
- finance teams need explainability and auditability rather than free-form chatbot output.

The strategic point is not "AI makes fraud solvable." It is that AI can handle semantic fragments that deterministic payment controls historically handled poorly, while deterministic controls still govern objective checks.

## 11. USP failure conditions

The positioning fails if research shows that:

- target buyers already have an incumbent that supplies the same evidence workflow;
- customers will not add a pre-payment step;
- manual uploads are considered unacceptable even for pilot use;
- bank-ownership verification is the only capability buyers value;
- case review takes longer than existing procedures;
- AI explanation adds noise rather than clarity.

These are reasons to change the product, not reasons to rewrite the marketing.


## External references

Research snapshot: **2026-09-19**. Market and technology facts can change; re-check before public claims or fundraising material.

1. Association for Financial Professionals, **2025 Payments Fraud and Control Survey Report** — 79% of surveyed organizations reported attempted or actual payments fraud in 2024; BEC remained the leading avenue.  
   https://www.afponline.org/training-resources/resources/survey-research-economic-data/details/payments-fraud
2. AFP press release, **79% of Organizations Were Victims of Attempted or Actual Payments Fraud Activity in 2024** — BEC cited by 63%; vendor-imposter fraud cited by 45%, up 11 percentage points from the previous survey.  
   https://www.afponline.org/about/learn-more/press-releases/Details/survey-79-percent-of-organizations-were-victims-of-attempted-or-actual-payments-fraud-activity-in-2024
3. FBI, **2025 IC3 Annual Report** — 24,768 BEC complaints and approximately $3.047B in reported BEC losses in 2025.  
   https://www.fbi.gov/file-repository/2025_ic3report.pdf
4. NVIDIA, **Nemotron 3 Ultra / NIM** — `nvidia/nemotron-3-ultra-550b-a55b` is available through NVIDIA's hosted API endpoint; self-hosting requires datacenter-class GPUs and is not a target for this project.  
   https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b
5. Strands Agents, **Model Providers** — Strands is provider-agnostic and supports custom/community providers including NVIDIA NIM; it runs in the application process rather than requiring an AWS-hosted control plane.  
   https://strandsagents.com/docs/user-guide/concepts/model-providers/
6. Cedar Policy Language documentation — Cedar is an authorization policy language; it should be used for access-control decisions, not as the fraud-scoring engine.  
   https://docs.cedarpolicy.com/
7. Finch README — current Windows prerequisites specify an AMD64-based Windows system; this is a compatibility issue for Windows-on-ARM/Snapdragon development machines.  
   https://github.com/runfinch/finch/blob/main/README.md
