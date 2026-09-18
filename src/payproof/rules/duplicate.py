from ..domain.enums import FindingOrigin, FindingSeverity, FindingStatus
from ..domain.models import Finding
from .base import CaseContext, VerificationRule

class DuplicateInvoiceRule:
    rule_id: str = "INVOICE_001_DUPLICATE"
    version: str = "1.0.0"

    def evaluate(self, ctx: CaseContext) -> list[Finding]:
        inv_ref = ctx.get_field_val("invoice_reference") or ctx.case.invoice_reference
        ev_id = ctx.get_field_evidence_id("invoice_reference")
        ev_ids = [ev_id] if ev_id else []

        if not inv_ref:
            return []

        clean_ref = inv_ref.strip().upper().replace(" ", "").replace("-", "").replace("/", "")

        # Check against payment history
        for p in ctx.payment_history:
            history_ref = p.invoice_ref.strip().upper().replace(" ", "").replace("-", "").replace("/", "")
            if clean_ref == history_ref:
                return [
                    Finding(
                        case_id=ctx.case.id,
                        rule_id=self.rule_id,
                        severity=FindingSeverity.CRITICAL,
                        status=FindingStatus.FAIL,
                        title=f"Duplicate Invoice Detected: '{inv_ref}'",
                        explanation=(
                            f"Invoice reference '{inv_ref}' was already paid on {p.paid_date} "
                            f"under payment ID '{p.payment_id}' for amount {p.currency} {p.amount}. "
                            f"Submitting this payment risks duplicate disbursement."
                        ),
                        evidence_ids=ev_ids,
                        origin=FindingOrigin.DETERMINISTIC,
                        metadata={"duplicate_payment_id": p.payment_id, "paid_date": p.paid_date}
                    )
                ]

        return [
            Finding(
                case_id=ctx.case.id,
                rule_id=self.rule_id,
                severity=FindingSeverity.LOW,
                status=FindingStatus.PASS,
                title="Invoice Reference Unique",
                explanation=f"Invoice reference '{inv_ref}' does not match any previously paid invoices in vendor history.",
                evidence_ids=ev_ids,
                origin=FindingOrigin.DETERMINISTIC,
            )
        ]
