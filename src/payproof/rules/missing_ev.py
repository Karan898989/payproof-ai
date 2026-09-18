from ..domain.enums import FindingOrigin, FindingSeverity, FindingStatus
from ..domain.models import Finding
from .base import CaseContext, VerificationRule

class MissingBaselineRule:
    rule_id: str = "EVIDENCE_001_MISSING_BASELINE"
    version: str = "1.0.0"

    def evaluate(self, ctx: CaseContext) -> list[Finding]:
        if not ctx.vendor:
            return [
                Finding(
                    case_id=ctx.case.id,
                    rule_id=self.rule_id,
                    severity=FindingSeverity.HIGH,
                    status=FindingStatus.FAIL,
                    title="Missing Verified Vendor Baseline",
                    explanation="No verified vendor baseline or trusted banking records exist in the system for this payee.",
                    evidence_ids=[],
                    origin=FindingOrigin.DETERMINISTIC,
                )
            ]
        return []

class MissingVerificationRule:
    rule_id: str = "EVIDENCE_002_MISSING_VERIFICATION"
    version: str = "1.0.0"

    def evaluate(self, ctx: CaseContext) -> list[Finding]:
        inv_account = ctx.get_field_val("invoice_account_number")
        email_account = ctx.get_field_val("email_claimed_account")

        # Determine if there is an unverified account present
        target_account = email_account or inv_account
        if not target_account or not ctx.vendor:
            return []

        known_last4s = {acc.account_number_last4 for acc in ctx.vendor.accounts}
        acc_last4 = target_account.strip()[-4:]

        is_new_account = acc_last4 not in known_last4s

        # If it's a new account, check whether independent callback verification has been recorded
        if is_new_account:
            if not ctx.verification_callback or not ctx.verification_callback.is_confirmed:
                return [
                    Finding(
                        case_id=ctx.case.id,
                        rule_id=self.rule_id,
                        severity=FindingSeverity.HIGH,
                        status=FindingStatus.FAIL,
                        title="Independent Vendor Callback Verification Missing",
                        explanation=(
                            f"Beneficiary bank account changed to '*{acc_last4}'. Policy mandates an independent out-of-band "
                            f"phone verification using the trusted vendor contact ({ctx.vendor.contact_name} at {ctx.vendor.contact_phone}) "
                            f"before funds may be released."
                        ),
                        evidence_ids=[],
                        origin=FindingOrigin.DETERMINISTIC,
                        metadata={
                            "trusted_contact_name": ctx.vendor.contact_name,
                            "trusted_contact_phone": ctx.vendor.contact_phone,
                            "claimed_account_last4": acc_last4,
                        }
                    )
                ]
            else:
                return [
                    Finding(
                        case_id=ctx.case.id,
                        rule_id=self.rule_id,
                        severity=FindingSeverity.LOW,
                        status=FindingStatus.PASS,
                        title="Independent Vendor Callback Completed",
                        explanation=(
                            f"Out-of-band verification completed by {ctx.verification_callback.verified_by} "
                            f"via phone {ctx.verification_callback.callback_phone_used} with {ctx.verification_callback.vendor_contact_spoken}."
                        ),
                        evidence_ids=[],
                        origin=FindingOrigin.DETERMINISTIC,
                    )
                ]

        return []
