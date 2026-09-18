---
title: "PayProof AI — Market Requirements Document"
document: MRD
version: "0.1"
status: "Market-validation baseline"
date: "2026-09-19"
---

# PayProof AI — Market Requirements Document

## 1. Market definition

PayProof AI sits at the intersection of:

- accounts-payable controls;
- vendor/supplier verification;
- business email compromise mitigation;
- payment-fraud prevention;
- invoice/PO reconciliation;
- finance workflow auditability.

It should **not** initially position itself as a full AP automation platform or as a bank-account verification network. Those markets contain mature products with data/network advantages that a new local-first MVP does not possess.

The initial wedge is narrower:

> **An integration-light evidence verification layer for finance teams that still reconcile vendor payment-change evidence manually across email, invoices, purchase orders, vendor-master data and transaction history.**

## 2. Evidence that the problem is material

The market need is real, but the presence of a real problem does not automatically prove a new product will win.

Current evidence:

- AFP's 2025 Payments Fraud and Control Survey reports that **79% of surveyed organizations experienced attempted or actual payments fraud in 2024**.
- The same AFP reporting identifies **business email compromise as the leading avenue**, cited by 63% of respondents.
- AFP reported **vendor-imposter fraud at 45% of respondents**, an 11-percentage-point increase from the prior survey.
- The FBI's 2025 IC3 report lists **24,768 BEC complaints** and about **$3.047 billion in reported BEC losses** for 2025.

These numbers demonstrate a substantial problem. They do **not** establish PayProof's addressable market, conversion rate, or product-market fit.

## 3. Market reality: this category is not empty

Several established products already address overlapping problems.

### Eftsure
Public positioning includes independent verification of payee identity and bank details, continuous re-verification when information changes, payment-file screening and a verified-vendor network.

**Implication:** PayProof cannot claim that "nobody verifies bank-detail changes."

### PaymentWorks
Public positioning includes vendor onboarding, bank-account verification, fraud controls, ERP integration, permissions and auditable vendor updates.

**Implication:** PayProof cannot claim unique ownership of controlled vendor onboarding or bank-change verification.

### Trustmi
Public positioning includes behavioral AI, a trust network, vendor validation, evidence/reasoning for approvers, and continuous monitoring of vendor/bank changes.

**Implication:** "AI agent + evidence + vendor-change detection" is not unique by itself.

### Medius Fraud & Risk Detection
Public positioning includes invoice verification, anomaly detection, segregation of duties, risk summaries and ERP-integrated AP fraud controls.

**Implication:** PayProof cannot win simply by showing an AI risk dashboard.

## 4. Competitive gap worth testing

The defensible near-term opportunity is **not** "better AI."

The proposed gap is:

1. **integration-light start** — usable from exports and files before a deep ERP project;
2. **case-centric evidence dossier** — one review object containing email, invoice, PO, vendor baseline and history;
3. **deterministic-first findings** — explainable rules are first-class rather than hidden behind a generic score;
4. **missing/contradictory evidence as an output** — uncertainty is surfaced instead of converted into false precision;
5. **policy-aware human gate** — the product manages what verification is required before payment can proceed;
6. **portable/local evaluation path** — organizations can evaluate the workflow without sending the entire finance stack to a new SaaS platform.

This combination is plausible as a wedge, but it is **not yet a proven moat**. Customer interviews must validate whether these characteristics are important enough to switch, pay or adopt.

## 5. Ideal customer profile

### 5.1 Initial ICP

Target organizations with the following process characteristics:

- recurring B2B vendor payments;
- vendor banking changes are currently received through email/forms;
- AP staff manually compare multiple systems/files;
- maker-checker or manager approval exists but evidence is fragmented;
- accounting/ERP exports can be obtained even if APIs are not available;
- the organization does not already have a mature beneficiary-verification network integrated into its payment process;
- payment errors/fraud are high-consequence enough to justify a pre-payment control;
- team is willing to add a verification step for changed/high-risk payments.

This process-based ICP is more useful than choosing customers only by employee count.

### 5.2 Early buyer

**Economic buyer:** Controller, Head of Finance, CFO, Head of AP or Treasury leader.

**Primary user:** AP analyst / finance operations analyst.

**Secondary user:** finance approver, internal audit, security/fraud team.

### 5.3 Poor-fit customers for initial release

Do not target first:

- enterprises already standardized on Eftsure/PaymentWorks/Trustmi/Medius or equivalent;
- companies demanding direct bank-account ownership verification on day one;
- organizations requiring certified regulated payment processing;
- extremely small businesses with only a handful of invoices and no approval workflow;
- customers requiring on-prem production support before the product has security/compliance maturity.

## 6. High-value use cases

Priority order:

### MR-UC1 — Vendor beneficiary change
A known supplier requests payment to a new bank account.

**Why first:** high consequence, easy to demonstrate, directly connected to BEC/vendor impersonation risk.

### MR-UC2 — Invoice before first payment to new beneficiary
A payment is being prepared for an account never previously used for that vendor.

### MR-UC3 — Duplicate or altered invoice
Invoice reference or amount conflicts with prior invoice/payment history.

### MR-UC4 — Email/invoice/PO contradiction
The documents are individually plausible but disagree on vendor identity, currency, amount or account.

### MR-UC5 — Approval-claim verification
An email claims that a senior person already approved a change, but the case has no recorded approval evidence.

## 7. Buyer pain map

| Pain | Current workaround | Failure mode | Product requirement |
|---|---|---|---|
| Bank detail changes arrive by email | manual phone call / spreadsheet note | wrong number used, call not recorded, step skipped | force verification-required state and capture completion evidence |
| AP checks several systems | tab switching / memory | mismatch overlooked | unified evidence dossier |
| Approver gets only a summary message | trust analyst's judgment | weak evidence trace | source-linked findings |
| Fraud tools give opaque score | manually interpret | poor trust / poor auditability | deterministic reasons + raw evidence |
| Workflow differs by employee | informal SOP | control drift | versioned decision rules and authorization |
| AI can be persuasive but wrong | human reads prose | hallucinated facts become decisions | AI-derived facts marked and constrained |

## 8. Market requirements

### MR-001 — Must fit existing workflows before deep integration
The product must deliver value from file/CSV/email inputs. Integrations improve adoption later but must not be required to prove the core workflow.

### MR-002 — Must preserve human accountability
Finance users need a decision-support product, not an autonomous agent with authority to pay vendors.

### MR-003 — Must be explainable to non-ML users
Every hold/review state must have specific evidence-backed reasons.

### MR-004 — Must support independent verification
A bank-detail change workflow must explicitly require independent confirmation where configured.

### MR-005 — Must support maker-checker controls
Different users/roles must have different authority.

### MR-006 — Must generate audit evidence
A buyer must be able to reconstruct what happened during a payment review.

### MR-007 — Must fail safely
Model or connector failure must not silently downgrade a risk.

### MR-008 — Must eventually integrate
Commercial viability beyond demos requires connectors to accounting/ERP, email and external validation sources.

### MR-009 — Must be deployable securely
A commercial version will need SSO, tenant isolation, encryption, backup, retention controls, security monitoring and compliance work. Local MVP quality must not be described as production security.

## 9. Beachhead market recommendation

The initial market-validation cohort should be:

> **SMB and mid-market AP/finance teams with meaningful B2B payment volume, manual/semi-manual vendor-change workflows, and no existing specialized beneficiary-verification platform.**

The first sales conversation should focus on **changed beneficiary details and pre-payment evidence review**, not on broad "AI fraud prevention."

Why this beachhead:

- pain is concrete;
- the trigger event is identifiable;
- product value can be demonstrated on a single case;
- files/exports are enough for an MVP;
- the buyer already understands payment controls;
- deployment can start as an assistive workflow before full ERP integration.

## 10. Geography

The product architecture should remain jurisdiction-neutral in BUILD IT.

Do **not** lock the MVP to a country-specific bank format beyond pluggable validators.

Go-to-market geography should be chosen only after interviews. Bank-account ownership, business registry, sanctions and tax verification are jurisdiction/provider dependent and will materially change the product.

For market validation, English-language finance teams are the lowest-friction starting point because the current UI/model workflow is English-first.

## 11. Competitive positioning matrix

| Capability | PayProof BUILD IT | Eftsure | PaymentWorks | Trustmi | Medius |
|---|---:|---:|---:|---:|---:|
| Local/no-AWS evaluation | **Yes** | Not core positioning | Not core positioning | Not core positioning | Not core positioning |
| Manual file/CSV evidence case | **Core** | Partial/varies | Onboarding/workflow centric | Vendor/payment centric | AP platform centric |
| Bank-account ownership network | **No** | **Core strength** | Available | Available/partner intelligence | Not equivalent |
| Deterministic source-linked findings | **Core design** | Some verification evidence | Verification/status | Evidence/reasoning | Risk factors |
| Explicit missing-evidence state | **Core design** | Not clear from public material | Partial | Partial | Partial |
| AI semantic evidence reasoning | Planned/core bounded use | Product dependent | Product dependent | Yes | Yes |
| Full ERP/AP suite | **No** | Integrates | Vendor management | Integrates | **Yes** |
| Human approval/audit workflow | Yes | Yes | Yes | Yes | Yes |

**Interpretation:** incumbents are strong. PayProof's near-term advantage can only come from a sharper workflow, lower integration friction, trustworthy evidence handling and rapid deployment—not from claiming a category they already serve.

## 12. Market entry strategy

### Stage A — Workflow discovery
Before building integrations:

- interview 15-20 AP/finance practitioners;
- ask for their actual bank-change procedure;
- identify which evidence sources they consult;
- identify where verification is recorded;
- measure approximate review time;
- identify previous near-misses without collecting confidential details.

### Stage B — Clickable/local pilot
Demonstrate:

- create case;
- upload evidence;
- highlight new account + domain mismatch;
- show missing independent verification;
- produce audit dossier.

Primary question:

> "Would this replace or materially improve any step you perform today?"

### Stage C — Design partners
Recruit 3-5 organizations willing to provide sanitized/synthetic examples modeled on real workflows.

Do not ingest production banking data until security, legal and privacy controls are ready.

### Stage D — First connector
Choose **one** connector based on demand, not developer preference.

Candidate categories:

- accounting/ERP export;
- Microsoft 365/Gmail;
- vendor-master source;
- external beneficiary verification provider.

## 13. Pricing hypothesis

Do not set final pricing before buyer interviews.

The most plausible commercial model is:

**base subscription + verification volume tier + optional premium connectors**

because value scales with payment/vendor volume and integration depth.

Avoid:

- per-token AI pricing exposed to the buyer;
- charging only per user if the core value is transaction control;
- a low-price consumer model;
- indemnification claims without insurance/legal structure.

Possible pilot structure:

- time-boxed evaluation using synthetic/sanitized data;
- fixed pilot fee or free design-partner program;
- no long-term price promise until usage and willingness-to-pay are measured.

## 14. Market-validation metrics

| Question | Evidence threshold |
|---|---|
| Is vendor-change verification a recurring pain? | majority of qualified interviews describe a real control/workflow |
| Is fragmented evidence materially costly? | users can identify time/error/rework caused by cross-system review |
| Is integration-light valuable? | design partners will test before a deep ERP integration |
| Does source-linked reasoning matter? | reviewers prefer/need evidence trace over generic score |
| Will someone pay? | at least several qualified buyers agree to a paid pilot or give credible budget/approval path |
| Is the product replacing a real step? | pilot users use it in a defined workflow, not only as a demo |

Do not treat compliments, hackathon votes, signups without use, or social engagement as product-market fit.

## 15. Go/no-go criteria after discovery

### Continue
Proceed if:

- the beneficiary-change workflow is common enough in the target cohort;
- users can provide or export the required evidence;
- reviewers report that consolidation/explainability solves a real workflow problem;
- at least 3 design partners agree to test;
- no dominant incumbent is already deployed in most target organizations.

### Pivot
Pivot the workflow if:

- bank changes are too rare;
- existing tools already solve the complete flow;
- customers value external bank verification far more than evidence fusion;
- the product creates too much review friction.

Potential pivots:

- evidence/audit layer that sits on top of existing verification products;
- AP exception triage;
- vendor onboarding evidence consistency;
- internal controls audit automation.

### Stop
Stop this product direction if customers consistently say the only missing capability is proprietary bank-network verification that cannot be obtained economically, and they do not value the evidence/workflow layer independently.

## 16. Market claims allowed vs prohibited

### Allowed after implementation proof
- "Consolidates invoice, vendor, PO and payment-history evidence into one review case."
- "Flags configured inconsistencies such as new beneficiary details or duplicate invoice references."
- "Uses human-in-the-loop approval."
- "Runs locally in BUILD IT mode without AWS."

### Not allowed without external evidence
- "Prevents payment fraud."
- "Stops BEC."
- "Detects 99% of fraudulent invoices."
- "Verifies bank-account ownership."
- "Guarantees safe payments."
- "Industry-first."
- "World's first."
- "Best fraud platform."

## 17. Market research backlog

Before SHIP IT, complete:

1. 15-20 customer interviews;
2. competitor demo/trial comparison where legally accessible;
3. pricing interviews;
4. regulatory/privacy review for intended geography;
5. external beneficiary-verification provider landscape;
6. accounting/ERP integration prioritization;
7. security questionnaire expectations from finance buyers;
8. data-retention requirements;
9. procurement friction and expected SOC 2/ISO requirements;
10. bottom-up TAM/SAM/SOM model using a clearly defined ICP.

Do not create a top-down billion-dollar TAM slide from adjacent "fraud detection" market reports. It would be too broad to be decision-useful.


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


## Additional competitor references

- Eftsure: https://www.eftsure.com/
- PaymentWorks: https://www.paymentworks.com/what-we-do/
- Trustmi vendor onboarding and management: https://trustmi.ai/products/vendor-onboarding-and-management/
- Medius Fraud & Risk Detection: https://www.medius.com/solutions/fraud-risk-detection/
