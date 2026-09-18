# PayProof AI — Pre-Payment Verification System

**PayProof AI** is a local-first, evidence-bound pre-payment decision support system for Accounts Payable and Finance teams. It enforces multi-evidence consistency checks before funds disbursement to prevent Business Email Compromise (BEC), vendor imposter fraud, unauthorized banking changes, and duplicate disbursement.

---

## Key Features

1. **Single Entry Point (`run.py` / `run.bat`)**:
   - One-click launcher that verifies/installs dependencies, initializes SQLite, seeds benchmark demo cases, launches the server, and automatically opens your browser to `http://127.0.0.1:8000`.

2. **Deterministic-First Verification Engine**:
   - `BENEFICIARY_001_NEW_ACCOUNT`: Flags unknown bank accounts not in the verified baseline.
   - `DOMAIN_001_UNRECOGNIZED_SENDER`: Detects emails from unapproved sender domains.
   - `DOMAIN_002_LOOKALIKE`: Identifies typosquatted and lookalike sender domains.
   - `INVOICE_001_DUPLICATE`: Reconciles invoice references against historical disbursements.
   - `PO_001_MISMATCH`: 3-way matching on currency, vendor, and amount limits.
   - `AMOUNT_001_OUTLIER`: Robust statistical outlier detection using Median Absolute Deviation (MAD).
   - `EVIDENCE_001_MISSING_BASELINE`: Flags un-onboarded vendors.
   - `EVIDENCE_002_MISSING_VERIFICATION`: Enforces independent phone callback proof on banking changes.

3. **NVIDIA Nemotron 3 Ultra Integration**:
   - Model: `nvidia/nemotron-3-ultra-550b-a55b` via hosted NVIDIA NIM API.
   - Extracts semantic intent, quotes, urgency, and contradictions between email and invoices.
   - **Degrades safely**: Operates seamlessly in pure deterministic mode if offline or without an API key.

4. **Cedar Authorization & IAM**:
   - Native Cedar policy engine with roles:
     - **Analyst**: Create cases, ingest evidence, trigger analysis. Cannot override holds.
     - **Approver**: Review cases, record callbacks, override holds with justification, approve release.
     - **Auditor**: Strict read-only access to cases, export dossiers, and audit trails.
     - **Admin**: Full system management.
   - Live IAM role switcher built directly into the web UI.

5. **Tamper-Evident Audit Dossier**:
   - Cryptographic SHA-256 hash-chained event trail.
   - One-click exportable JSON audit dossier.

---

## Quick Start

### Option 1: Double-Click (Windows)
Double-click `run.bat` in the project root folder.

### Option 2: Command Line
```powershell
python run.py
```

The system will:
1. Validate requirements (`fastapi`, `uvicorn`, `pydantic`, `pypdf`, `pyyaml`, `jinja2`, etc.).
2. Seed the 3 demo benchmark scenarios into `.var/payproof.db`.
3. Open your default web browser to `http://127.0.0.1:8000`.

---

## Exploring the Benchmark Scenarios

Once the web application opens:

- **Demo A — Normal Safe Invoice (`DEMO-A-NORMAL`)**:
  - Legitimate freight invoice from Apex Logistics Corp matching Purchase Order and verified bank baseline.
  - Outcome: `CLEAR_FOR_STANDARD_APPROVAL`.

- **Demo B — Vendor Bank Change Notification (`DEMO-B-BANK-CHANGE`)**:
  - Global Steel Inc requests payment to a new bank account.
  - Outcome: `INDEPENDENT_VENDOR_VERIFICATION_REQUIRED`.
  - Use the Reviewer Workbench to record an out-of-band callback and observe the status update.

- **Demo C — Phishing BEC Spoof Attack (`DEMO-C-BEC-ATTACK`)**:
  - Spoofed sender domain (`apexloglstics.com`), unverified bank account, and urgent demand.
  - Outcome: `PAYMENT_HOLD`.
  - Test Cedar IAM: try overriding as Analyst (blocked), then switch to Approver and submit a justified override.

---

## Running Tests

Run the full automated test suite with:

```powershell
python -m pytest tests/ -v
```
