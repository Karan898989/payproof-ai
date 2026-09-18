from decimal import Decimal
from ..domain.enums import FindingOrigin, FindingSeverity, FindingStatus
from ..domain.models import Finding
from .base import CaseContext, VerificationRule

class POMatchRule:
    rule_id: str = "PO_001_MISMATCH"
    version: str = "1.0.0"

    def evaluate(self, ctx: CaseContext) -> list[Finding]:
        if not ctx.purchase_order:
            return [
                Finding(
                    case_id=ctx.case.id,
                    rule_id=self.rule_id,
                    severity=FindingSeverity.MEDIUM,
                    status=FindingStatus.UNKNOWN,
                    title="No Associated Purchase Order Found",
                    explanation="No purchase order was attached or linked to this payment case for three-way matching.",
                    evidence_ids=[],
                    origin=FindingOrigin.DETERMINISTIC,
                )
            ]

        po = ctx.purchase_order
        case_amount = ctx.case.amount
        case_curr = ctx.case.currency.upper()
        po_curr = po.currency.upper()

        ev_id = ctx.get_field_evidence_id("invoice_amount")
        ev_ids = [ev_id] if ev_id else []

        # 1. Currency mismatch
        if case_curr != po_curr:
            return [
                Finding(
                    case_id=ctx.case.id,
                    rule_id=self.rule_id,
                    severity=FindingSeverity.HIGH,
                    status=FindingStatus.FAIL,
                    title=f"Currency Mismatch with PO {po.po_number}",
                    explanation=f"Case currency '{case_curr}' does not match Purchase Order currency '{po_curr}'.",
                    evidence_ids=ev_ids,
                    origin=FindingOrigin.DETERMINISTIC,
                    metadata={"case_currency": case_curr, "po_currency": po_curr}
                )
            ]

        # 2. Amount mismatch (invoice amount exceeds PO amount)
        if case_amount > po.amount:
            diff = case_amount - po.amount
            pct = (diff / po.amount) * 100 if po.amount > 0 else Decimal(100)
            return [
                Finding(
                    case_id=ctx.case.id,
                    rule_id=self.rule_id,
                    severity=FindingSeverity.HIGH,
                    status=FindingStatus.FAIL,
                    title=f"Invoice Amount Exceeds PO {po.po_number}",
                    explanation=(
                        f"Invoice amount ({case_curr} {case_amount}) exceeds Purchase Order authorized limit "
                        f"({po_curr} {po.amount}) by {case_curr} {diff} ({pct:.1f}% over PO limit)."
                    ),
                    evidence_ids=ev_ids,
                    origin=FindingOrigin.DETERMINISTIC,
                    metadata={"invoice_amount": str(case_amount), "po_amount": str(po.amount), "difference": str(diff)}
                )
            ]

        # 3. Valid match
        return [
            Finding(
                case_id=ctx.case.id,
                rule_id=self.rule_id,
                severity=FindingSeverity.LOW,
                status=FindingStatus.PASS,
                title=f"Purchase Order Match: {po.po_number}",
                explanation=f"Invoice amount ({case_curr} {case_amount}) is within approved PO limit ({po_curr} {po.amount}).",
                evidence_ids=ev_ids,
                origin=FindingOrigin.DETERMINISTIC,
            )
        ]
