from pathlib import Path
import yaml
from uuid import uuid4
from ..domain.enums import DecisionState, FindingSeverity, FindingStatus
from ..domain.models import Decision, Finding
from ..config import settings

class DecisionEngine:
    def __init__(self, policy_path: Path | None = None):
        self.policy_path = policy_path or settings.decision_policy_path
        self.policy = self._load_policy()

    def _load_policy(self) -> dict:
        if self.policy_path.exists():
            with open(self.policy_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def decide(self, case_id: str, findings: list[Finding]) -> Decision:
        findings_map = {f.rule_id: f for f in findings}

        # Check hard hold conditions
        # 1. New account + unrecognized sender
        new_acc = findings_map.get("BENEFICIARY_001_NEW_ACCOUNT")
        unrec_domain = findings_map.get("DOMAIN_001_UNRECOGNIZED_SENDER")
        lookalike = findings_map.get("DOMAIN_002_LOOKALIKE")
        duplicate = findings_map.get("INVOICE_001_DUPLICATE")

        is_hard_hold = False
        reasons = []
        actions = []

        if lookalike and lookalike.status == FindingStatus.FAIL:
            is_hard_hold = True
            reasons.append("LOOKALIKE_DOMAIN_SPOOFING")
            actions.append("Freeze case; notify Infosec team of suspected BEC attack")

        if new_acc and new_acc.status == FindingStatus.FAIL and unrec_domain and unrec_domain.status == FindingStatus.FAIL:
            is_hard_hold = True
            reasons.append("NEW_ACCOUNT_AND_UNRECOGNIZED_SENDER")
            actions.append("Hold payment immediately; do not disburse to unauthorized beneficiary")

        if duplicate and duplicate.status == FindingStatus.FAIL:
            is_hard_hold = True
            reasons.append("DUPLICATE_INVOICE_REFERENCE")
            actions.append("Verify whether this invoice was already paid in ERP history")

        if is_hard_hold:
            return Decision(
                id=str(uuid4()),
                case_id=case_id,
                state=DecisionState.PAYMENT_HOLD,
                reason_codes=reasons,
                required_actions=actions,
                rule_version="2026-09-19.1",
            )

        # Check independent verification required
        # If new account or missing verification
        missing_verif = findings_map.get("EVIDENCE_002_MISSING_VERIFICATION")
        if (new_acc and new_acc.status == FindingStatus.FAIL) or (missing_verif and missing_verif.status == FindingStatus.FAIL):
            return Decision(
                id=str(uuid4()),
                case_id=case_id,
                state=DecisionState.INDEPENDENT_VENDOR_VERIFICATION_REQUIRED,
                reason_codes=["BENEFICIARY_CHANGE_UNVERIFIED"],
                required_actions=[
                    "Conduct out-of-band phone callback using verified contact number from vendor master",
                    "Do NOT use any phone number provided in the incoming email or invoice",
                    "Record callback verification in PayProof before releasing payment"
                ],
                rule_version="2026-09-19.1",
            )

        # Check review required
        po_mismatch = findings_map.get("PO_001_MISMATCH")
        amount_outlier = findings_map.get("AMOUNT_001_OUTLIER")
        missing_baseline = findings_map.get("EVIDENCE_001_MISSING_BASELINE")

        review_reasons = []
        review_actions = []

        if po_mismatch and po_mismatch.status == FindingStatus.FAIL:
            review_reasons.append("PO_DISCREPANCY")
            review_actions.append("Resolve PO pricing/currency variance with Procurement team")

        if amount_outlier and amount_outlier.status == FindingStatus.FAIL:
            review_reasons.append("HISTORICAL_AMOUNT_OUTLIER")
            review_actions.append("Review whether invoice scope/contract amendment justifies elevated amount")

        if missing_baseline and missing_baseline.status == FindingStatus.FAIL:
            review_reasons.append("VENDOR_NOT_ONBOARDED")
            review_actions.append("Onboard vendor into Vendor Master and establish banking baseline")

        # Any other failed high/critical findings
        for f in findings:
            if f.status == FindingStatus.FAIL and f.severity in (FindingSeverity.HIGH, FindingSeverity.CRITICAL):
                if f.rule_id not in findings_map:
                    review_reasons.append(f.rule_id)

        if review_reasons:
            return Decision(
                id=str(uuid4()),
                case_id=case_id,
                state=DecisionState.REVIEW_REQUIRED,
                reason_codes=review_reasons,
                required_actions=review_actions or ["Review flagged discrepancies before approval"],
                rule_version="2026-09-19.1",
            )

        # Clear for standard approval
        return Decision(
            id=str(uuid4()),
            case_id=case_id,
            state=DecisionState.CLEAR_FOR_STANDARD_APPROVAL,
            reason_codes=["ALL_EVIDENCE_CONSISTENT"],
            required_actions=["Proceed to standard accounts payable approval and disbursement schedule"],
            rule_version="2026-09-19.1",
        )

decision_engine = DecisionEngine()
