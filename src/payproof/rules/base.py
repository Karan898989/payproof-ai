from typing import Protocol, runtime_checkable
from pydantic import BaseModel
from ..domain.models import (
    PaymentCase, EvidenceObject, ProvenancedField, Finding,
    VendorBaseline, PurchaseOrder, PaymentHistoryRecord, VerificationCallbackRecord
)

class CaseContext(BaseModel):
    case: PaymentCase
    evidence: list[EvidenceObject]
    fields: list[ProvenancedField]
    vendor: VendorBaseline | None = None
    purchase_order: PurchaseOrder | None = None
    payment_history: list[PaymentHistoryRecord] = []
    verification_callback: VerificationCallbackRecord | None = None

    def get_field_val(self, name: str) -> str | None:
        for f in self.fields:
            if f.name == name:
                return f.normalized_value or f.raw_value
        return None

    def get_field_evidence_id(self, name: str) -> str | None:
        for f in self.fields:
            if f.name == name:
                return f.evidence_id
        return None

@runtime_checkable
class VerificationRule(Protocol):
    rule_id: str
    version: str

    def evaluate(self, ctx: CaseContext) -> list[Finding]:
        """Evaluates the rule against the case context and returns findings."""
        ...
