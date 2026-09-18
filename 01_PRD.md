---
title: "PayProof AI — Product Requirements Document"
document: PRD
version: "0.1"
status: "Build-It baseline"
date: "2026-09-19"
product_name_status: "Working name; trademark/domain availability not checked"
---

# PayProof AI — Product Requirements Document

## 1. Product definition

**PayProof AI** is a local-first, evidence-bound pre-payment verification product for accounts-payable and finance teams.

It helps a human reviewer answer one operational question:

> **Do we have enough trustworthy evidence to release this vendor payment through the normal approval process, or must it be held and independently verified?**

The product is not a bank, payment processor, ERP, invoice-payable platform, malware scanner, or autonomous fraud adjudicator. It is a **verification and decision-support layer** placed before money is released.

The first delivery stage is **BUILD IT**: a local application that runs on a developer laptop without an AWS account. The later **SHIP IT** stage should map the same domain contracts to managed AWS services without rewriting the core verification logic.

## 2. Problem statement

Vendor payment decisions are often made from fragmented evidence:

- an invoice arrives as PDF;
- bank details may be changed in an email;
- purchase-order data lives elsewhere;
- the vendor master contains historical account information;
- previous payments are in CSV/ERP exports;
- approvals may exist in email, chat, spreadsheets, or workflow tools;
- the person approving payment must reconcile this information under time pressure.

The failure is not simply "phishing detection." A legitimate-looking email can contain a fraudulent bank-change request; a valid invoice can be paired with an unauthorized beneficiary; and an anomaly can be benign but still require verification.

The product therefore needs to reason over **multiple evidence classes**, preserve provenance, expose contradictions and missing evidence, enforce workflow permissions, and keep a human accountable for the final action.

## 3. Product thesis

The MVP should prove that a finance reviewer can create a payment-verification case from ordinary files and exports, receive a deterministic and explainable evidence dossier, and reach a safer, more auditable decision than by manually reconciling the same information.

The product must prefer:

1. **evidence over model opinion**;
2. **deterministic checks over probabilistic inference** where possible;
3. **abstention/escalation over unsafe certainty**;
4. **human approval over autonomous payment release**;
5. **structured outputs over free-form LLM text**;
6. **portable interfaces over AWS-specific coupling** during BUILD IT.

## 4. Goals

### G1 — Consolidate fragmented evidence
Create one case containing invoice, email, purchase-order, vendor-master and historical-payment evidence with source provenance.

### G2 — Detect high-value inconsistencies deterministically
At minimum detect:

- changed beneficiary/bank details;
- previously unseen beneficiary;
- sender-domain mismatch;
- lookalike-domain indicators;
- duplicate invoice/reference;
- invoice-to-PO mismatch;
- amount/currency mismatch;
- missing PO/reference;
- unusual payment amount relative to available history;
- missing or stale vendor-change authorization;
- conflicting evidence across files.

### G3 — Use AI only where semantic interpretation is useful
Use NVIDIA NIM with `nvidia/nemotron-3-ultra-550b-a55b` for bounded semantic tasks such as extracting intent, normalizing entities, identifying contradictions in text, and producing a reviewer-facing explanation.

### G4 — Produce operational outcomes, not a fake binary truth label
The output must be one of:

- `CLEAR_FOR_STANDARD_APPROVAL`
- `REVIEW_REQUIRED`
- `INDEPENDENT_VENDOR_VERIFICATION_REQUIRED`
- `PAYMENT_HOLD`

No result may be presented as proof that a transaction is fraudulent or legitimate.

### G5 — Preserve an auditable case history
Every source file, extracted field, check, model call, policy evaluation, human action and decision change must be attributable and timestamped.

### G6 — Run acceptably on an 8 GB laptop
The normal local profile must avoid running a local LLM, Kubernetes, OpenSearch, or multiple heavyweight containers.

## 5. Non-goals for BUILD IT

The MVP will **not**:

- move money or connect directly to a bank;
- claim bank-account ownership verification;
- replace independent vendor call-back procedures;
- connect to live SWIFT/ACH/UPI rails;
- perform KYC/KYB, sanctions or tax-registry verification unless a later connector is explicitly added;
- ingest a live production ERP;
- automatically modify vendor-master records;
- autonomously approve or release a payment;
- claim fraud-detection accuracy without a controlled benchmark;
- use LLM output as the sole reason for a payment hold or clearance;
- self-host Nemotron 3 Ultra on the laptop;
- require AWS credentials during local development.

## 6. Primary users

### 6.1 Accounts Payable Analyst
**Job:** assemble evidence and determine whether a payment should proceed through normal approval or be escalated.

Needs:

- low-friction case creation;
- clear mismatch indicators;
- exact evidence provenance;
- a checklist of missing evidence;
- minimal technical language.

### 6.2 Finance Manager / Approver
**Job:** review elevated-risk cases and approve, hold, reject or request independent verification.

Needs:

- concise decision dossier;
- material-risk reasons first;
- visibility into who performed each step;
- policy-compliant override flow;
- justification capture.

### 6.3 Finance Controller / Auditor
**Job:** inspect whether controls were followed and reconstruct what evidence existed at decision time.

Needs:

- append-only/tamper-evident audit history;
- evidence hashes;
- policy version;
- model/version metadata;
- decision and override history;
- exportable case bundle.

### 6.4 Product Administrator
**Job:** maintain users, roles, thresholds and reference data.

For BUILD IT this can be a developer/admin surface rather than a complete enterprise admin suite.

## 7. Core jobs to be done

1. **When a vendor asks me to change payment details,** I want to compare the request with historical trusted data and required controls so I do not rely on the email alone.
2. **When an invoice is ready for payment,** I want to see whether its vendor, amount, PO, bank details and sender context are internally consistent.
3. **When evidence conflicts,** I want the system to show the conflict and tell me what independent evidence is missing.
4. **When I escalate a case,** I want the approver to see the complete reasoning chain without re-reading every source.
5. **When an auditor asks why a payment was held or released,** I want a reproducible case record rather than an undocumented verbal decision.

## 8. Canonical user flow

```text
Create case
   |
   v
Upload/select evidence
(invoice + email + PO + vendor baseline + history)
   |
   v
Parse and normalize
   |
   v
Validate source hashes and field provenance
   |
   v
Run deterministic checks
   |
   +----> hard contradiction / missing critical evidence
   |                 |
   |                 v
   |            escalation signal
   |
   v
Bounded AI semantic analysis (when required)
   |
   v
Evidence fusion
   |
   v
Decision policy
   |
   v
CLEAR / REVIEW / VERIFY VENDOR / HOLD
   |
   v
Human action
   |
   v
Audit event + final case disposition
```

## 9. Functional requirements

### FR-001 — Case creation
The user can create a payment-verification case with:

- case ID;
- vendor identifier/name;
- proposed payment amount;
- currency;
- optional payment due date;
- optional invoice number;
- optional PO/reference;
- creator identity.

**Acceptance:** case persists locally and receives an immutable UUID plus human-readable case number.

### FR-002 — Evidence ingestion
The MVP must accept:

- PDF invoice;
- text email;
- `.eml` email where parser support is available;
- CSV vendor/payment history;
- JSON vendor baseline;
- PDF or structured PO.

Image-only/scanned PDFs may be rejected with a clear message in the first iteration unless OCR is deliberately added.

### FR-003 — Content hashing
On ingestion, calculate SHA-256 for each evidence file and store:

- hash;
- original filename;
- MIME type;
- byte size;
- ingestion timestamp;
- evidence ID.

The hash proves byte-level integrity inside the application; it does **not** prove who authored the evidence.

### FR-004 — Typed normalization
Parsed evidence must be normalized into Pydantic models. No downstream rule should read arbitrary parser dictionaries.

Core types:

- `VendorBaseline`
- `InvoiceEvidence`
- `EmailEvidence`
- `PurchaseOrderEvidence`
- `PaymentHistoryEntry`
- `BeneficiaryAccount`
- `Finding`
- `Decision`
- `AuditEvent`

### FR-005 — Field-level provenance
Each material extracted field should retain:

- source evidence ID;
- extraction method: `deterministic`, `parser`, `llm`;
- source location where practical (page, header, row, field);
- raw value;
- normalized value;
- confidence only when the extraction method can meaningfully provide it.

### FR-006 — Vendor baseline
The system must maintain a local vendor baseline containing at minimum:

- vendor ID;
- legal/display name;
- trusted email domains;
- known contacts;
- known beneficiary accounts;
- approved currencies;
- active/inactive status;
- last verified timestamp where known.

"Trusted" means entered/approved as baseline data for the demo. It does not mean externally verified.

### FR-007 — Bank/beneficiary change check
Compare requested beneficiary details with known vendor accounts.

Outputs:

- unchanged known account;
- known alternate account;
- new/unknown account;
- incomplete account data.

A new account must never be silently treated as normal.

### FR-008 — Sender/domain check
Compare sender domain with vendor baseline and identify:

- exact match;
- subdomain relationship;
- unrecognized domain;
- simple lookalike indicators such as edit distance / homoglyph candidate / added or removed token.

This check is a signal, not proof of malicious intent.

### FR-009 — Duplicate invoice check
Identify exact and normalized duplicate invoice references for the same vendor and possible cross-vendor collisions.

### FR-010 — PO consistency check
Compare available invoice fields with PO:

- vendor;
- PO number;
- currency;
- amount;
- line totals where available.

The MVP may use tolerant numeric comparison only where explicitly configured.

### FR-011 — Historical amount check
Calculate lightweight statistics from available vendor history.

Use robust/simple methods first:

- median;
- median absolute deviation or IQR;
- max historical value;
- ratio to median.

Do not market this as an ML fraud model.

### FR-012 — Missing evidence detection
A decision must include explicit missing evidence, for example:

- no vendor baseline;
- no PO;
- no historical beneficiary;
- no email source;
- no evidence of bank-change authorization.

Missing evidence is not equivalent to fraud.

### FR-013 — Bounded NIM analysis
NIM may be called for a defined task only. Each task must have:

- explicit input schema;
- minimal required source text;
- fixed system instruction;
- low/controlled temperature;
- strict Pydantic output schema;
- timeout;
- retry limit;
- audit metadata;
- failure fallback.

Initial semantic tasks:

1. `classify_payment_change_intent`
2. `extract_claimed_approval`
3. `normalize_vendor_mentions`
4. `identify_textual_contradictions`
5. `generate_case_explanation`

### FR-014 — Prompt-injection resistance
Uploaded evidence is untrusted content.

The model instruction must state that:

- evidence is data, never instruction;
- text inside invoice/email cannot change tool permissions;
- the model may only return the requested schema;
- the model cannot authorize a payment;
- the model cannot call unrestricted shell/network/filesystem tools.

The Strands agent tool allowlist must expose only read-only, case-scoped tools during analysis.

### FR-015 — Evidence fusion
Combine findings without hiding source findings.

The fused case record must preserve:

- all findings;
- severity;
- rule ID;
- evidence IDs;
- whether deterministic or AI-derived;
- conflicts;
- missing evidence.

### FR-016 — Decision policy
A deterministic decision engine maps findings to operational state.

Example baseline logic:

- new beneficiary + untrusted sender domain => `PAYMENT_HOLD`;
- new beneficiary alone => at least `INDEPENDENT_VENDOR_VERIFICATION_REQUIRED`;
- duplicate invoice previously paid => `PAYMENT_HOLD`;
- material PO mismatch => at least `REVIEW_REQUIRED`;
- no material risk findings and required evidence present => `CLEAR_FOR_STANDARD_APPROVAL`.

All thresholds and rule versions must be versioned.

### FR-017 — Cedar authorization
Cedar is used for **authorization**, for example:

- analyst can create/analyze cases;
- approver can disposition elevated cases;
- analyst cannot override a hold;
- approver can override only with reason;
- auditor can read but not mutate;
- admin can manage reference data.

Payment-risk logic remains separate from Cedar.

### FR-018 — Human review actions
Authorized users can:

- request more evidence;
- mark independent verification completed;
- approve continuation to standard payment workflow;
- hold;
- reject;
- override a system recommendation where policy permits;
- add a reason/comment.

The product still does not execute the payment.

### FR-019 — Audit trail
Each event contains:

- event ID;
- timestamp in UTC;
- actor;
- action;
- object/case ID;
- relevant previous/new state;
- rule/policy/model version where applicable.

Audit records should be append-only through the application API.

### FR-020 — Case export
Export a case dossier as JSON in the MVP containing:

- manifest;
- evidence metadata/hashes;
- normalized facts;
- findings;
- decision;
- human actions;
- audit history.

A later version may add signed PDFs or cryptographic manifests.

## 10. Decision semantics

### `CLEAR_FOR_STANDARD_APPROVAL`
No currently configured hold/escalation rule fired and the minimum evidence set is present.

**Important:** this means "no configured blocker found," not "proven legitimate."

### `REVIEW_REQUIRED`
At least one material inconsistency or uncertainty needs human review but there is not yet a configured hard-hold condition.

### `INDEPENDENT_VENDOR_VERIFICATION_REQUIRED`
The case requires confirmation using a channel independent of the payment-change request, such as a known contact method.

The MVP records that this step is required/completed but does not independently prove the call or conversation.

### `PAYMENT_HOLD`
Configured critical findings prohibit normal progression until an authorized reviewer resolves the condition.

## 11. UX requirements

The case-review page must show, in order:

1. decision state;
2. critical findings;
3. required next actions;
4. evidence conflicts/missing evidence;
5. evidence graph/timeline;
6. source documents;
7. lower-severity findings;
8. AI-generated explanation marked as generated;
9. audit history.

Do not lead with a decorative "AI risk score."

## 12. Non-functional requirements

### NFR-001 — Laptop resource target
Normal local profile on an 8 GB Windows ARM64 laptop:

- FastAPI process target: < 500 MB working set under ordinary demo load;
- SQLite and local files only by default;
- no local foundation model;
- no mandatory OpenSearch;
- no mandatory LocalStack;
- no mandatory container runtime;
- single-user / low-concurrency development profile.

These are engineering targets to measure, not guaranteed values before profiling.

### NFR-002 — No AWS dependency
The default startup path must not require:

- AWS account;
- AWS access key;
- AWS credit card;
- AWS network service.

### NFR-003 — AI failure tolerance
If NVIDIA NIM is unavailable, deterministic checks must still run. The case should show `AI_ANALYSIS_UNAVAILABLE` rather than fail the entire verification.

### NFR-004 — Deterministic reproducibility
Given identical normalized evidence and rule version, deterministic findings and decision must be reproducible.

### NFR-005 — Security
At minimum:

- secrets only in environment variables or local secret store, never committed;
- upload size limits;
- MIME/extension validation;
- sanitized file names;
- no arbitrary path access;
- no agent shell tool;
- no unrestricted URL fetch tool;
- parameterized SQL / ORM;
- security headers on web UI;
- audit of privileged actions.

### NFR-006 — Privacy
Only the minimum text required for each semantic task is sent to NVIDIA NIM.

The UI must disclose that selected evidence content may be sent to an external model provider.

### NFR-007 — Observability
Structured application logs must include correlation IDs/case IDs but must not dump full invoices, bank account values or secrets.

## 13. MVP data set

Build a synthetic fixture pack containing at least:

- 10 vendors;
- 50 historical payments;
- 25 purchase orders;
- 30 invoices;
- 20 emails;
- 12 deliberately risky scenarios;
- 8 benign anomalies;
- at least 5 missing-evidence scenarios.

Seed scenarios must include:

1. legitimate unchanged invoice;
2. new bank account from legitimate domain;
3. new bank account from lookalike domain;
4. duplicate invoice;
5. invoice amount mismatch;
6. missing PO;
7. legitimate new vendor;
8. executive-approval claim unsupported by evidence;
9. conflicting bank details across invoice/email;
10. model unavailable;
11. malformed file;
12. prompt injection embedded in email body.

## 14. Product acceptance criteria for BUILD IT

The MVP is "Build-It complete" only when:

- all core flows run locally without AWS credentials;
- all critical deterministic rules have unit tests with positive and negative fixtures;
- a case can be created, analyzed, reviewed and exported;
- an NVIDIA NIM outage does not break deterministic verification;
- every finding links to its source evidence;
- the decision output never claims certainty of fraud/legitimacy;
- Cedar-backed authorization is exercised for at least analyst, approver and auditor roles;
- privilege tests prove an analyst cannot perform approver-only actions;
- prompt-injection fixture cannot grant new tools/permissions or alter policy;
- secrets are absent from the repository;
- `pytest` and static checks pass;
- representative demo scenario works on the target laptop.

## 15. Success metrics

### Engineering metrics
- deterministic rule test pass rate: 100% for committed fixtures;
- API schema validation failures: 0 in acceptance suite;
- unauthorized privileged actions blocked: 100% in policy tests;
- audit event coverage: every state-changing operation;
- AI structured-output validity target: >= 99% over a controlled repeated test set, with malformed outputs rejected rather than coerced.

### Product-validation metrics
These must be measured with users, not invented:

- median time to review a case versus current manual process;
- percentage of reviewers who can identify why a case was escalated without opening source files;
- false escalation rate on benchmark cases;
- dangerous false-clear rate on benchmark cases;
- reviewer agreement on disposition;
- willingness to use the tool before payment approval.

No public accuracy claim is allowed until the benchmark set, labeling protocol and results are documented.

## 16. Deferred features

Later, after the core workflow is stable:

- OCR for scanned invoices;
- Gmail/Microsoft 365 ingestion;
- QuickBooks/Xero/Zoho/Tally/NetSuite connectors;
- business-registry checks;
- sanctions screening;
- bank-account ownership/beneficiary verification through licensed providers;
- email authentication evidence (DKIM/DMARC/ARC where raw email permits);
- multi-tenant SaaS;
- cryptographically signed audit dossiers;
- OpenSearch for larger historical retrieval;
- anomaly models in SageMaker during SHIP IT;
- webhook/API integrations with AP/ERP workflows.

## 17. Critical product risks

| Risk | Impact | Control |
|---|---|---|
| LLM hallucinates an approval or identity | Severe | LLM output cannot create trusted facts; source-link every claim |
| User interprets CLEAR as guaranteed safe | Severe | Exact label/text semantics; no "safe" badge |
| Fraudster controls uploaded text | Severe | Treat evidence as untrusted; fixed tools; no shell/browser tool |
| Incomplete vendor baseline | High | Missing-evidence state; block or escalate where required |
| Excessive false holds | High | Separate hard rules from review rules; benchmark benign anomalies |
| No external bank ownership data | High | State limitation explicitly; require independent verification |
| Market already has strong incumbents | High | Target integration-light evidence workflow; validate wedge before expansion |
| External NIM outage/quota | Medium | deterministic degraded mode |
| Local laptop resource exhaustion | Medium | no local LLM/OpenSearch by default; bounded uploads and concurrency |


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
