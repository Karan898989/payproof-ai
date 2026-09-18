from decimal import Decimal
import statistics
from ..domain.enums import FindingOrigin, FindingSeverity, FindingStatus
from ..domain.models import Finding
from .base import CaseContext, VerificationRule

class AmountHistoryRule:
    rule_id: str = "AMOUNT_001_OUTLIER"
    version: str = "1.0.0"

    def evaluate(self, ctx: CaseContext) -> list[Finding]:
        if len(ctx.payment_history) < 3:
            return [
                Finding(
                    case_id=ctx.case.id,
                    rule_id=self.rule_id,
                    severity=FindingSeverity.INFO,
                    status=FindingStatus.UNKNOWN,
                    title="Insufficient Payment History for Outlier Detection",
                    explanation=f"Only {len(ctx.payment_history)} prior payments recorded for vendor; minimum 3 required for statistical baseline.",
                    evidence_ids=[],
                    origin=FindingOrigin.DETERMINISTIC,
                )
            ]

        amounts = [float(p.amount) for p in ctx.payment_history]
        median_val = statistics.median(amounts)
        deviations = [abs(x - median_val) for x in amounts]
        mad = statistics.median(deviations)

        case_amt = float(ctx.case.amount)
        ev_id = ctx.get_field_evidence_id("invoice_amount")
        ev_ids = [ev_id] if ev_id else []

        # Outlier threshold: case_amt > median + 3.5 * MAD (or 3x median if MAD is 0)
        threshold = median_val + (3.5 * mad) if mad > 0 else (median_val * 3.0)

        if case_amt > threshold:
            ratio = case_amt / median_val if median_val > 0 else 0
            return [
                Finding(
                    case_id=ctx.case.id,
                    rule_id=self.rule_id,
                    severity=FindingSeverity.HIGH,
                    status=FindingStatus.FAIL,
                    title="Statistical Amount Outlier Detected",
                    explanation=(
                        f"Invoice amount ({ctx.case.currency} {ctx.case.amount}) is {ratio:.1f}x the historical median "
                        f"({ctx.case.currency} {median_val:.2f}, threshold {threshold:.2f}). "
                        f"This payment significantly exceeds typical disbursements for this vendor."
                    ),
                    evidence_ids=ev_ids,
                    origin=FindingOrigin.DETERMINISTIC,
                    metadata={"historical_median": median_val, "threshold": threshold, "sample_size": len(amounts)}
                )
            ]

        return [
            Finding(
                case_id=ctx.case.id,
                rule_id=self.rule_id,
                severity=FindingSeverity.LOW,
                status=FindingStatus.PASS,
                title="Payment Amount Consistent with History",
                explanation=f"Amount ({ctx.case.currency} {ctx.case.amount}) is within normal variance of historical payments (median: {ctx.case.currency} {median_val:.2f}).",
                evidence_ids=ev_ids,
                origin=FindingOrigin.DETERMINISTIC,
            )
        ]
