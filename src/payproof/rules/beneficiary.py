import hashlib
from ..domain.enums import FindingOrigin, FindingSeverity, FindingStatus
from ..domain.models import Finding
from .base import CaseContext, VerificationRule

class BeneficiaryChangeRule:
    rule_id: str = "BENEFICIARY_001_NEW_ACCOUNT"
    version: str = "1.0.0"

    def evaluate(self, ctx: CaseContext) -> list[Finding]:
        findings = []
        # Check both invoice account and email claimed account
        inv_account = ctx.get_field_val("invoice_account_number")
        email_account = ctx.get_field_val("email_claimed_account")

        target_accounts = []
        if inv_account:
            target_accounts.append(("Invoice", inv_account, ctx.get_field_evidence_id("invoice_account_number")))
        if email_account and email_account != inv_account:
            target_accounts.append(("Email", email_account, ctx.get_field_evidence_id("email_claimed_account")))

        if not target_accounts:
            return [
                Finding(
                    case_id=ctx.case.id,
                    rule_id=self.rule_id,
                    severity=FindingSeverity.INFO,
                    status=FindingStatus.NOT_APPLICABLE,
                    title="No Beneficiary Account Extracted",
                    explanation="No bank account or IBAN was extracted from uploaded invoice or email evidence.",
                    evidence_ids=[],
                    origin=FindingOrigin.DETERMINISTIC,
                )
            ]

        if not ctx.vendor:
            # Missing baseline handled by EVIDENCE_001
            return []

        known_last4s = {acc.account_number_last4 for acc in ctx.vendor.accounts}
        known_hashes = {acc.full_account_hash for acc in ctx.vendor.accounts}

        for source, account_str, ev_id in target_accounts:
            clean_acc = account_str.strip()
            acc_hash = hashlib.sha256(clean_acc.encode()).hexdigest()
            acc_last4 = clean_acc[-4:] if len(clean_acc) >= 4 else clean_acc

            is_match = (acc_hash in known_hashes) or (acc_last4 in known_last4s)

            ev_ids = [ev_id] if ev_id else []

            if not is_match:
                findings.append(
                    Finding(
                        case_id=ctx.case.id,
                        rule_id=self.rule_id,
                        severity=FindingSeverity.CRITICAL,
                        status=FindingStatus.FAIL,
                        title=f"New/Unverified Beneficiary Account in {source}",
                        explanation=(
                            f"Account ending in '*{acc_last4}' specified in {source} does NOT match any "
                            f"verified baseline account for vendor '{ctx.vendor.name}'. "
                            f"Known accounts end in: {', '.join('*' + a for a in known_last4s) if known_last4s else 'None'}."
                        ),
                        evidence_ids=ev_ids,
                        origin=FindingOrigin.DETERMINISTIC,
                        metadata={
                            "source": source,
                            "claimed_account_last4": acc_last4,
                            "known_accounts_count": len(ctx.vendor.accounts),
                        }
                    )
                )
            else:
                findings.append(
                    Finding(
                        case_id=ctx.case.id,
                        rule_id=self.rule_id,
                        severity=FindingSeverity.LOW,
                        status=FindingStatus.PASS,
                        title=f"Verified Beneficiary Account in {source}",
                        explanation=f"Account ending in '*{acc_last4}' in {source} matches verified baseline for '{ctx.vendor.name}'.",
                        evidence_ids=ev_ids,
                        origin=FindingOrigin.DETERMINISTIC,
                    )
                )

        return findings
