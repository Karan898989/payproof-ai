import json
from decimal import Decimal
from datetime import datetime
from typing import Any
from ..domain.enums import CaseState, DecisionState, EvidenceType, FindingOrigin, FindingSeverity, FindingStatus, RoleName
from ..domain.models import (
    PaymentCase, EvidenceObject, ProvenancedField, Finding, Decision, AuditEvent,
    VendorBaseline, VendorAccount, PurchaseOrder, PaymentHistoryRecord, VerificationCallbackRecord, User
)
from .db import get_db

class CaseRepository:
    # Users
    def create_user(self, user: User) -> None:
        with get_db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (id, username, full_name, role, email) VALUES (?, ?, ?, ?, ?)",
                (user.id, user.username, user.full_name, user.role.value, user.email)
            )

    def get_user_by_username(self, username: str) -> User | None:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if not row:
                return None
            return User(
                id=row["id"],
                username=row["username"],
                full_name=row["full_name"],
                role=RoleName(row["role"]),
                email=row["email"]
            )

    def list_users(self) -> list[User]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM users").fetchall()
            return [
                User(
                    id=r["id"],
                    username=r["username"],
                    full_name=r["full_name"],
                    role=RoleName(r["role"]),
                    email=r["email"]
                )
                for r in rows
            ]

    # Vendor Baseline
    def save_vendor(self, vendor: VendorBaseline) -> None:
        with get_db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO vendors (vendor_id, name, trusted_domains, contact_phone, contact_name) VALUES (?, ?, ?, ?, ?)",
                (vendor.vendor_id, vendor.name, json.dumps(vendor.trusted_domains), vendor.contact_phone, vendor.contact_name)
            )
            for acc in vendor.accounts:
                conn.execute(
                    """INSERT OR REPLACE INTO vendor_accounts 
                    (id, vendor_id, bank_name, routing_number, account_number_last4, full_account_hash, status, effective_from)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (acc.id, acc.vendor_id, acc.bank_name, acc.routing_number, acc.account_number_last4, acc.full_account_hash, acc.status, acc.effective_from.isoformat())
                )

    def get_vendor(self, vendor_id: str) -> VendorBaseline | None:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM vendors WHERE vendor_id = ?", (vendor_id,)).fetchone()
            if not row:
                return None
            accounts_rows = conn.execute("SELECT * FROM vendor_accounts WHERE vendor_id = ?", (vendor_id,)).fetchall()
            accounts = [
                VendorAccount(
                    id=ar["id"],
                    vendor_id=ar["vendor_id"],
                    bank_name=ar["bank_name"],
                    routing_number=ar["routing_number"],
                    account_number_last4=ar["account_number_last4"],
                    full_account_hash=ar["full_account_hash"],
                    status=ar["status"],
                    effective_from=datetime.fromisoformat(ar["effective_from"]),
                )
                for ar in accounts_rows
            ]
            return VendorBaseline(
                vendor_id=row["vendor_id"],
                name=row["name"],
                trusted_domains=json.loads(row["trusted_domains"]),
                accounts=accounts,
                contact_phone=row["contact_phone"],
                contact_name=row["contact_name"],
            )

    # Purchase Orders
    def save_po(self, po: PurchaseOrder) -> None:
        with get_db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO purchase_orders (po_number, vendor_id, vendor_name, amount, currency, status) VALUES (?, ?, ?, ?, ?, ?)",
                (po.po_number, po.vendor_id, po.vendor_name, str(po.amount), po.currency, po.status)
            )

    def get_po(self, po_number: str) -> PurchaseOrder | None:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM purchase_orders WHERE po_number = ?", (po_number,)).fetchone()
            if not row:
                return None
            return PurchaseOrder(
                po_number=row["po_number"],
                vendor_id=row["vendor_id"],
                vendor_name=row["vendor_name"],
                amount=Decimal(row["amount"]),
                currency=row["currency"],
                status=row["status"],
            )

    def get_po_by_vendor(self, vendor_id: str) -> PurchaseOrder | None:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM purchase_orders WHERE vendor_id = ? LIMIT 1", (vendor_id,)).fetchone()
            if not row:
                return None
            return PurchaseOrder(
                po_number=row["po_number"],
                vendor_id=row["vendor_id"],
                vendor_name=row["vendor_name"],
                amount=Decimal(row["amount"]),
                currency=row["currency"],
                status=row["status"],
            )

    # Payment History
    def save_payment_history(self, records: list[PaymentHistoryRecord]) -> None:
        with get_db() as conn:
            for r in records:
                conn.execute(
                    """INSERT OR REPLACE INTO payment_history 
                    (payment_id, vendor_id, amount, currency, paid_date, invoice_ref, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (r.payment_id, r.vendor_id, str(r.amount), r.currency, r.paid_date, r.invoice_ref, r.status)
                )

    def get_payment_history_for_vendor(self, vendor_id: str) -> list[PaymentHistoryRecord]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM payment_history WHERE vendor_id = ?", (vendor_id,)).fetchall()
            return [
                PaymentHistoryRecord(
                    payment_id=r["payment_id"],
                    vendor_id=r["vendor_id"],
                    amount=Decimal(r["amount"]),
                    currency=r["currency"],
                    paid_date=r["paid_date"],
                    invoice_ref=r["invoice_ref"],
                    status=r["status"],
                )
                for r in rows
            ]

    # Cases
    def create_case(self, case: PaymentCase) -> None:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO cases 
                (id, case_number, vendor_id, vendor_name, invoice_reference, amount, currency, state, created_by, created_at, updated_at, rule_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    case.id, case.case_number, case.vendor_id, case.vendor_name, case.invoice_reference,
                    str(case.amount), case.currency, case.state.value, case.created_by,
                    case.created_at.isoformat(), case.updated_at.isoformat(), case.rule_version
                )
            )

    def update_case(self, case: PaymentCase) -> None:
        with get_db() as conn:
            conn.execute(
                """UPDATE cases SET
                    vendor_id = ?, vendor_name = ?, invoice_reference = ?, amount = ?,
                    currency = ?, state = ?, updated_at = ?
                WHERE id = ?""",
                (
                    case.vendor_id, case.vendor_name, case.invoice_reference,
                    str(case.amount), case.currency, case.state.value,
                    datetime.now().isoformat(), case.id
                )
            )

    def get_case(self, case_id: str) -> PaymentCase | None:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM cases WHERE id = ? OR case_number = ?", (case_id, case_id)).fetchone()
            if not row:
                return None
            return PaymentCase(
                id=row["id"],
                case_number=row["case_number"],
                vendor_id=row["vendor_id"],
                vendor_name=row["vendor_name"],
                invoice_reference=row["invoice_reference"],
                amount=Decimal(row["amount"]),
                currency=row["currency"],
                state=CaseState(row["state"]),
                created_by=row["created_by"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                rule_version=row["rule_version"],
            )

    def list_cases(self) -> list[PaymentCase]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
            return [
                PaymentCase(
                    id=r["id"],
                    case_number=r["case_number"],
                    vendor_id=r["vendor_id"],
                    vendor_name=r["vendor_name"],
                    invoice_reference=r["invoice_reference"],
                    amount=Decimal(r["amount"]),
                    currency=r["currency"],
                    state=CaseState(r["state"]),
                    created_by=r["created_by"],
                    created_at=datetime.fromisoformat(r["created_at"]),
                    updated_at=datetime.fromisoformat(r["updated_at"]),
                    rule_version=r["rule_version"],
                )
                for r in rows
            ]

    # Evidence
    def add_evidence(self, evidence: EvidenceObject) -> None:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO evidence_objects 
                (id, case_id, evidence_type, original_filename, mime_type, sha256, byte_size, local_path, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    evidence.id, evidence.case_id, evidence.evidence_type.value,
                    evidence.original_filename, evidence.mime_type, evidence.sha256,
                    evidence.byte_size, evidence.local_path, evidence.ingested_at.isoformat()
                )
            )

    def list_evidence_for_case(self, case_id: str) -> list[EvidenceObject]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM evidence_objects WHERE case_id = ? ORDER BY ingested_at ASC", (case_id,)).fetchall()
            return [
                EvidenceObject(
                    id=r["id"],
                    case_id=r["case_id"],
                    evidence_type=EvidenceType(r["evidence_type"]),
                    original_filename=r["original_filename"],
                    mime_type=r["mime_type"],
                    sha256=r["sha256"],
                    byte_size=r["byte_size"],
                    local_path=r["local_path"],
                    ingested_at=datetime.fromisoformat(r["ingested_at"]),
                )
                for r in rows
            ]

    # Normalized Fields
    def save_normalized_fields(self, fields: list[ProvenancedField]) -> None:
        with get_db() as conn:
            for f in fields:
                conn.execute(
                    """INSERT OR REPLACE INTO normalized_fields
                    (id, case_id, name, raw_value, normalized_value, evidence_id, extraction_method, source_locator)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (f.id, f.case_id, f.name, f.raw_value, f.normalized_value, f.evidence_id, f.extraction_method, f.source_locator)
                )

    def get_normalized_fields(self, case_id: str) -> list[ProvenancedField]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM normalized_fields WHERE case_id = ?", (case_id,)).fetchall()
            return [
                ProvenancedField(
                    id=r["id"],
                    case_id=r["case_id"],
                    name=r["name"],
                    raw_value=r["raw_value"],
                    normalized_value=r["normalized_value"],
                    evidence_id=r["evidence_id"],
                    extraction_method=r["extraction_method"],
                    source_locator=r["source_locator"],
                )
                for r in rows
            ]

    # Findings
    def save_findings(self, case_id: str, findings: list[Finding]) -> None:
        with get_db() as conn:
            conn.execute("DELETE FROM findings WHERE case_id = ?", (case_id,))
            for f in findings:
                conn.execute(
                    """INSERT INTO findings
                    (id, case_id, rule_id, severity, status, title, explanation, evidence_ids, origin, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f.id, f.case_id, f.rule_id, f.severity.value, f.status.value,
                        f.title, f.explanation, json.dumps(f.evidence_ids), f.origin.value,
                        json.dumps(f.metadata), f.created_at.isoformat()
                    )
                )

    def get_findings_for_case(self, case_id: str) -> list[Finding]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM findings WHERE case_id = ? ORDER BY created_at ASC", (case_id,)).fetchall()
            return [
                Finding(
                    id=r["id"],
                    case_id=r["case_id"],
                    rule_id=r["rule_id"],
                    severity=FindingSeverity(r["severity"]),
                    status=FindingStatus(r["status"]),
                    title=r["title"],
                    explanation=r["explanation"],
                    evidence_ids=json.loads(r["evidence_ids"]),
                    origin=FindingOrigin(r["origin"]),
                    metadata=json.loads(r["metadata"]),
                    created_at=datetime.fromisoformat(r["created_at"]),
                )
                for r in rows
            ]

    # Decisions
    def save_decision(self, decision: Decision) -> None:
        with get_db() as conn:
            conn.execute("DELETE FROM decisions WHERE case_id = ?", (decision.case_id,))
            conn.execute(
                """INSERT INTO decisions
                (id, case_id, state, reason_codes, required_actions, ai_summary, ai_confidence, ai_intent_analysis, ai_contradictions, generated_at, rule_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    decision.id, decision.case_id, decision.state.value,
                    json.dumps(decision.reason_codes), json.dumps(decision.required_actions),
                    decision.ai_summary, decision.ai_confidence,
                    json.dumps(decision.ai_intent_analysis) if decision.ai_intent_analysis else None,
                    json.dumps(decision.ai_contradictions),
                    decision.generated_at.isoformat(), decision.rule_version
                )
            )

    def get_decision_for_case(self, case_id: str) -> Decision | None:
        with get_db() as conn:
            r = conn.execute("SELECT * FROM decisions WHERE case_id = ?", (case_id,)).fetchone()
            if not r:
                return None
            return Decision(
                id=r["id"],
                case_id=r["case_id"],
                state=DecisionState(r["state"]),
                reason_codes=json.loads(r["reason_codes"]),
                required_actions=json.loads(r["required_actions"]),
                ai_summary=r["ai_summary"],
                ai_confidence=r["ai_confidence"],
                ai_intent_analysis=json.loads(r["ai_intent_analysis"]) if r["ai_intent_analysis"] else None,
                ai_contradictions=json.loads(r["ai_contradictions"]) if r["ai_contradictions"] else [],
                generated_at=datetime.fromisoformat(r["generated_at"]),
                rule_version=r["rule_version"],
            )

    # Verification Callbacks
    def save_verification_callback(self, record: VerificationCallbackRecord) -> None:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO verification_callbacks 
                (id, case_id, verified_by, callback_phone_used, vendor_contact_spoken, confirmation_method, is_confirmed, notes, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.id, record.case_id, record.verified_by, record.callback_phone_used,
                    record.vendor_contact_spoken, record.confirmation_method, 1 if record.is_confirmed else 0,
                    record.notes, record.timestamp.isoformat()
                )
            )

    def get_verification_callback(self, case_id: str) -> VerificationCallbackRecord | None:
        with get_db() as conn:
            r = conn.execute("SELECT * FROM verification_callbacks WHERE case_id = ? ORDER BY timestamp DESC LIMIT 1", (case_id,)).fetchone()
            if not r:
                return None
            return VerificationCallbackRecord(
                id=r["id"],
                case_id=r["case_id"],
                verified_by=r["verified_by"],
                callback_phone_used=r["callback_phone_used"],
                vendor_contact_spoken=r["vendor_contact_spoken"],
                confirmation_method=r["confirmation_method"],
                is_confirmed=bool(r["is_confirmed"]),
                notes=r["notes"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
            )

    # Audit
    def save_audit_event(self, event: AuditEvent) -> None:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO audit_events 
                (id, case_id, actor_id, actor_role, event_type, timestamp, payload_redacted, previous_event_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.id, event.case_id, event.actor_id, event.actor_role,
                    event.event_type, event.timestamp.isoformat(),
                    json.dumps(event.payload_redacted), event.previous_event_hash, event.event_hash
                )
            )

    def get_last_audit_event(self) -> AuditEvent | None:
        with get_db() as conn:
            r = conn.execute("SELECT * FROM audit_events ORDER BY rowid DESC LIMIT 1").fetchone()
            if not r:
                return None
            return AuditEvent(
                id=r["id"],
                case_id=r["case_id"],
                actor_id=r["actor_id"],
                actor_role=r["actor_role"],
                event_type=r["event_type"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                payload_redacted=json.loads(r["payload_redacted"]),
                previous_event_hash=r["previous_event_hash"],
                event_hash=r["event_hash"],
            )

    def list_audit_events_for_case(self, case_id: str) -> list[AuditEvent]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM audit_events WHERE case_id = ? ORDER BY timestamp ASC", (case_id,)).fetchall()
            return [
                AuditEvent(
                    id=r["id"],
                    case_id=r["case_id"],
                    actor_id=r["actor_id"],
                    actor_role=r["actor_role"],
                    event_type=r["event_type"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    payload_redacted=json.loads(r["payload_redacted"]),
                    previous_event_hash=r["previous_event_hash"],
                    event_hash=r["event_hash"],
                )
                for r in rows
            ]

case_repo = CaseRepository()
