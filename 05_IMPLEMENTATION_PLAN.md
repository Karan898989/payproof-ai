---
title: "PayProof AI — Implementation Plan"
document: "Implementation Plan"
version: "0.1"
status: "Execution baseline"
date: "2026-09-19"
---

# PayProof AI — Implementation Plan

## 1. Implementation strategy

Build the product in vertical slices.

Do **not** start with:

- a dashboard;
- a chatbot;
- an architecture diagram implementation;
- AWS emulation;
- OpenSearch;
- multiple agents.

The first useful slice is:

> create case -> load trusted vendor baseline -> ingest invoice/email/PO -> run beneficiary/domain/duplicate/PO checks -> produce decision -> record human action.

AI is added only after that path is deterministic and tested.

## 2. Milestone overview

| Milestone | Outcome | Dependency |
|---|---|---|
| M0 | repository and engineering baseline | none |
| M1 | domain model + SQLite + case API | M0 |
| M2 | evidence ingestion + provenance | M1 |
| M3 | deterministic verification engine | M2 |
| M4 | decision engine + case review UI | M3 |
| M5 | NVIDIA NIM + Strands bounded semantic layer | M3 |
| M6 | Cedar authorization + human workflow | M4 |
| M7 | audit dossier + security hardening | M5, M6 |
| M8 | benchmark/demo fixtures + release gate | M7 |
| M9 | optional LocalStack/AWS adapter proof | M8 |

M9 is not required for the local MVP to function.

## 3. M0 — Engineering baseline

### Tasks
1. Create repository structure from System Specification.
2. Configure Python project with `pyproject.toml`.
3. Pin runtime/development dependencies.
4. Configure:
   - Ruff;
   - mypy;
   - pytest;
   - coverage.
5. Add `.env.example`.
6. Add secret patterns to `.gitignore`.
7. Add CI for:
   - lint;
   - type check;
   - tests;
   - package/import sanity.
8. Add architecture decision records:
   - ADR-001 modular monolith;
   - ADR-002 SQLite/local files;
   - ADR-003 deterministic-first;
   - ADR-004 hosted NIM;
   - ADR-005 Cedar only for authorization;
   - ADR-006 Finch ARM64 constraint.
9. Create synthetic-data policy: no real bank/account information in repository.

### Definition of done
- fresh clone installs;
- `pytest`, `ruff check`, and `mypy` pass;
- app starts and `/health/live` returns success;
- no AWS or NVIDIA credential is needed to start the app.

## 4. M1 — Domain model, repositories and case API

### Tasks
1. Implement enums:
   - case state;
   - evidence type;
   - decision state;
   - finding severity/status.
2. Implement Pydantic domain DTOs.
3. Implement SQL schema/migrations.
4. Implement repository ports.
5. Implement SQLite adapters.
6. Implement case service.
7. Implement API endpoints:
   - create case;
   - list cases;
   - read case.
8. Add request IDs and structured logging.
9. Seed one vendor and one sample case.

### Tests
- repository CRUD;
- invalid transitions;
- Decimal/currency serialization;
- duplicate case number prevention;
- API validation.

### Definition of done
A user can create and inspect a case from browser/API.

## 5. M2 — Evidence ingestion and provenance

### Tasks
1. Build secure upload endpoint.
2. Implement UUID-based evidence path storage.
3. Compute SHA-256.
4. Implement CSV/JSON parser first.
5. Implement text-based PDF parser.
6. Implement EML parser.
7. Implement normalization models.
8. Preserve field provenance.
9. Implement masking helpers.
10. Add unsupported/scanned-PDF state.

### Test fixtures
- valid invoice PDF;
- malformed PDF;
- oversized file;
- traversal filename;
- valid EML;
- HTML EML;
- vendor CSV;
- payment-history CSV;
- malformed CSV.

### Definition of done
A case can contain all required evidence types and every normalized material field points to source evidence.

## 6. M3 — Deterministic verification engine

Build rules in this order:

### Step 1 — Beneficiary checks
- known;
- new;
- missing;
- conflicting account between email and invoice.

### Step 2 — Sender/domain checks
- exact trusted domain;
- unknown domain;
- lookalike candidate.

### Step 3 — Duplicate invoice
- exact reference;
- normalized reference;
- already-paid state.

### Step 4 — PO checks
- vendor;
- currency;
- amount;
- missing PO.

### Step 5 — Historical amount checks
- insufficient history => unknown;
- median/IQR or MAD;
- configured threshold.

### Step 6 — Missing-evidence checks

### Engineering rule
Every rule must:

```text
input typed CaseContext
output list[Finding]
have stable rule_id
have version
have unit tests
contain no UI logic
contain no database writes
```

### Definition of done
All seeded high-risk and benign scenarios produce deterministic expected findings.

## 7. M4 — Decision engine and first complete user journey

### Tasks
1. Implement versioned YAML/typed decision configuration.
2. Validate decision config on startup.
3. Implement deterministic mapping from findings to decision state.
4. Implement review page.
5. Display:
   - decision;
   - critical findings;
   - source links;
   - missing evidence;
   - required actions.
6. Implement `analyze` workflow:
   - load case;
   - parse/normalize if needed;
   - run rules;
   - decide;
   - persist findings/decision.

### Critical UX constraint
Do not build a circular risk gauge as the primary element.

### Definition of done
A complete non-AI demo works:

```text
new bank account
+ unrecognized sender domain
=> PAYMENT_HOLD
```

with exact evidence shown.

This milestone proves the core product independently of an LLM.

## 8. M5 — NVIDIA NIM and Strands integration

### M5.1 Model adapter first
Implement `ModelProvider` interface with:

```text
analyze_payment_change_intent()
extract_claimed_approval()
find_textual_contradictions()
generate_case_explanation()
```

Write a fake provider for tests.

### M5.2 NVIDIA adapter
Configure NVIDIA hosted endpoint and model:

`nvidia/nemotron-3-ultra-550b-a55b`

Add:

- timeout;
- max retries;
- rate-limit handling;
- schema validation;
- response metadata;
- redaction.

### M5.3 Strands
Add one Strands agent with a strict read-only tool allowlist.

Do not start with multiple agents.

### M5.4 Structured output
Every task gets a Pydantic schema.

Do not parse critical results from natural-language prose with regex.

### M5.5 Degraded mode
Test:

- missing API key;
- timeout;
- 429;
- 500;
- invalid JSON;
- refusal;
- response exceeding allowed length.

Deterministic analysis must continue.

### Definition of done
AI adds semantic findings/explanation but cannot change trusted baseline, role permissions or payment authority.

## 9. M6 — Cedar authorization and human workflow

### M6.1 Cedar runtime spike
Because target hardware is Windows ARM64:

1. test official Cedar JS/WASM package on the target machine;
2. if successful, use it behind `AuthorizationPort`;
3. if not, compile/test the Rust CLI/runtime;
4. document the chosen path.

Do not block all earlier milestones on this spike.

### M6.2 Schema and policies
Implement:

- `User`;
- `Role`;
- `PaymentCase`;
- actions;
- role relationships.

### M6.3 Permission matrix tests

| Action | Analyst | Approver | Auditor | Admin |
|---|---:|---:|---:|---:|
| Create case | Allow | Allow | Deny | Allow |
| Analyze | Allow | Allow | Deny | Allow |
| Read | Allow | Allow | Allow | Allow |
| Record verification | Configurable | Allow | Deny | Allow |
| Override hold | Deny | Allow with context | Deny | configurable |
| Export | Allow | Allow | Allow | Allow |
| Manage baseline | Deny | configurable | Deny | Allow |

Exact policy may change, but explicit negative tests are mandatory.

### M6.4 Human actions
Implement:

- request verification;
- record verification result;
- hold;
- disposition;
- override with reason.

### Definition of done
Unauthorized calls fail server-side even if a UI button is manually invoked.

## 10. M7 — Audit, export and security hardening

### Audit
1. central audit service;
2. append-only API behavior;
3. hash-linked events;
4. audit every privileged mutation;
5. record decision/rule/model versions.

### Export
Create JSON dossier:

```text
manifest
case
evidence metadata
normalized facts
findings
decision
review actions
audit events
```

### Security
Add:

- CSRF/session protections as applicable;
- upload limits;
- MIME checks;
- path containment tests;
- secret scanning in CI;
- dependency audit;
- sanitized logs;
- security headers;
- prompt-injection fixtures;
- no shell/arbitrary HTTP tools.

### Definition of done
A reviewer can export a self-contained machine-readable case record and security tests pass.

## 11. M8 — Evaluation, regression pack and demo release

### M8.1 Synthetic benchmark
Minimum:

- 20 clearly safe/control scenarios;
- 20 risky/escalation scenarios;
- 10 ambiguous/missing-evidence scenarios.

Each fixture contains:

- expected deterministic findings;
- expected minimum decision state;
- rationale;
- evidence set.

Do not call this a real-world fraud benchmark.

### M8.2 Metrics
Report:

- rule-level precision/recall on seeded labels;
- decision confusion matrix;
- dangerous false-clear count;
- false-hold count;
- NIM schema failure rate;
- mean/median NIM latency;
- deterministic analysis latency;
- RAM profile.

Synthetic results must be labeled synthetic.

### M8.3 Demo scenarios

#### Demo A — Normal invoice
All baseline evidence matches.

#### Demo B — Vendor bank change
New account from normal vendor domain -> requires independent verification.

#### Demo C — High-risk contradiction
New account + lookalike/untrusted sender + claimed urgent approval -> hold.

Demo C must show that the LLM explanation is not the reason the hold fires; deterministic rules are.

### M8.4 Release gate
Required commands pass from a clean environment.

Create a reproducibility section in README.

## 12. M9 — Optional AWS-adapter proof

Only after the local product is stable.

### Goal
Prove that ports/adapters make SHIP IT possible without rewriting domain logic.

### Candidate adapter tests
- `EvidenceStore`: local -> LocalStack S3;
- repository subset: SQLite -> DynamoDB adapter;
- notifications -> SNS;
- background analysis -> SQS.

Do not migrate everything just to increase service count.

## 13. Recommended execution order by development day

This is an **estimate**, not a commitment.

### Day 1
M0 + core domain types.

### Day 2
SQLite repositories + case API.

### Day 3
CSV/JSON/PDF/EML ingestion and provenance.

### Day 4
Beneficiary/domain/duplicate rules.

### Day 5
PO/history/missing-evidence rules + decision engine.

### Day 6
Review UI + complete deterministic demo.

### Day 7
NVIDIA NIM adapter + schemas.

### Day 8
Strands orchestration + degraded mode + prompt-injection test.

### Day 9
Cedar integration + permissions + human workflow.

### Day 10
Audit/export + security hardening.

### Day 11
Synthetic benchmark + regression fixes.

### Day 12
Resource profiling + documentation + demo polish.

If schedule compresses, cut visual polish and optional integrations before cutting tests for payment decision/authorization paths.

## 14. Test gate per commit/PR

Minimum CI:

```text
ruff check .
mypy src
pytest -q
```

Coverage policy:

- target 90%+ on `rules/`, `decisioning`, `authz` core modules;
- a lower global threshold is acceptable initially if UI/parser code is still moving;
- never game the metric with meaningless tests.

## 15. Git/commit discipline

Use small, traceable commits:

```text
feat(domain): add payment case and evidence models
feat(ingest): add eml parser with provenance
feat(rules): detect new beneficiary account
test(rules): cover missing baseline and known alternate account
feat(authz): enforce approver-only hold override
fix(agent): reject malformed NIM structured output
```

Avoid single "upload complete project" commits.

## 16. Data and benchmark discipline

- synthetic account numbers only;
- no leaked/customer invoice dataset;
- provenance for any public dataset;
- train/validation/test separation if a learned model is ever added;
- no "accuracy" claim from hand-picked demo examples;
- retain failing examples as regression tests.

## 17. Build-versus-defer decisions

### Build now
- evidence ingestion;
- deterministic checks;
- provenance;
- decision state;
- NIM semantic tasks;
- authorization;
- audit;
- export.

### Defer
- OpenSearch;
- OCR unless essential;
- Gmail/Outlook;
- ERP integrations;
- bank verification;
- sanctions;
- multi-tenancy;
- payments;
- mobile app;
- custom ML model;
- dashboards with aggregate risk analytics.

## 18. Definition of MVP complete

The MVP is complete only when all are true:

- fresh local install works on the target machine;
- AWS credentials are unnecessary;
- no local LLM is needed;
- three demo scenarios reproduce reliably;
- deterministic rules are unit tested;
- NIM failure degrades safely;
- role authorization is enforced server-side;
- prompt-injection test cannot expand tool permissions;
- audit trail covers all state changes;
- export dossier is valid;
- source evidence is traceable from findings;
- no real financial secrets are committed;
- known limitations are documented.

## 19. Immediate first coding ticket

**Ticket: PP-001 — Establish domain contracts and end-to-end non-AI skeleton**

Deliver:

1. project scaffold;
2. `PaymentCase`, `EvidenceObject`, `Finding`, `Decision`, `AuditEvent`;
3. SQLite DB;
4. `POST /cases`;
5. `GET /cases/{id}`;
6. synthetic vendor baseline loader;
7. one deterministic `NEW_BENEFICIARY_ACCOUNT` rule;
8. one decision rule mapping new beneficiary -> independent verification required;
9. minimal HTML case result page;
10. tests.

This produces a real vertical slice before AI or infrastructure work.


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
