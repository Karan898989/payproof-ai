from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from .enums import CaseState, DecisionState, EvidenceType, FindingOrigin, FindingSeverity, FindingStatus, RoleName

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    full_name: str
    role: RoleName
    email: str

class PaymentCase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_number: str
    vendor_id: str | None = None
    vendor_name: str | None = None
    invoice_reference: str | None = None
    amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    state: CaseState = CaseState.DRAFT
    created_by: str = "analyst@example.com"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    rule_version: str = "2026-09-19.1"

class EvidenceObject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    evidence_type: EvidenceType
    original_filename: str
    mime_type: str
    sha256: str
    byte_size: int
    local_path: str
    ingested_at: datetime = Field(default_factory=utc_now)

class ProvenancedField(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    name: str
    raw_value: str | None = None
    normalized_value: str | None = None
    evidence_id: str | None = None
    extraction_method: Literal["parser", "deterministic", "llm"] = "parser"
    source_locator: str | None = None

class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    rule_id: str
    severity: FindingSeverity
    status: FindingStatus
    title: str
    explanation: str
    evidence_ids: list[str] = Field(default_factory=list)
    origin: FindingOrigin = FindingOrigin.DETERMINISTIC
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)

class Decision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    state: DecisionState
    reason_codes: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    ai_summary: str | None = None
    ai_confidence: str | None = None
    ai_intent_analysis: dict[str, Any] | None = None
    ai_contradictions: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=utc_now)
    rule_version: str = "2026-09-19.1"

class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str | None = None
    actor_id: str
    actor_role: str
    event_type: str
    timestamp: datetime = Field(default_factory=utc_now)
    payload_redacted: dict[str, Any] = Field(default_factory=dict)
    previous_event_hash: str | None = None
    event_hash: str = ""

class VendorAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    vendor_id: str
    bank_name: str
    routing_number: str
    account_number_last4: str
    full_account_hash: str
    status: Literal["active", "superseded", "frozen"] = "active"
    effective_from: datetime = Field(default_factory=utc_now)

class VendorBaseline(BaseModel):
    vendor_id: str
    name: str
    trusted_domains: list[str] = Field(default_factory=list)
    accounts: list[VendorAccount] = Field(default_factory=list)
    contact_phone: str = ""
    contact_name: str = ""

class PurchaseOrder(BaseModel):
    po_number: str
    vendor_id: str
    vendor_name: str
    amount: Decimal
    currency: str
    status: Literal["approved", "partially_fulfilled", "closed"] = "approved"

class PaymentHistoryRecord(BaseModel):
    payment_id: str
    vendor_id: str
    amount: Decimal
    currency: str
    paid_date: str
    invoice_ref: str
    status: Literal["completed", "reversed"] = "completed"

class VerificationCallbackRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    verified_by: str
    callback_phone_used: str
    vendor_contact_spoken: str
    confirmation_method: str
    is_confirmed: bool
    notes: str
    timestamp: datetime = Field(default_factory=utc_now)
