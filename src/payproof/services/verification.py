from ..domain.models import Finding
from ..rules.base import CaseContext, VerificationRule
from ..rules.beneficiary import BeneficiaryChangeRule
from ..rules.sender_domain import SenderDomainRule, LookalikeDomainRule
from ..rules.duplicate import DuplicateInvoiceRule
from ..rules.po_match import POMatchRule
from ..rules.amount import AmountHistoryRule
from ..rules.missing_ev import MissingBaselineRule, MissingVerificationRule

class VerificationEngine:
    def __init__(self, rules: list[VerificationRule] | None = None):
        if rules is None:
            self.rules = [
                BeneficiaryChangeRule(),
                SenderDomainRule(),
                LookalikeDomainRule(),
                DuplicateInvoiceRule(),
                POMatchRule(),
                AmountHistoryRule(),
                MissingBaselineRule(),
                MissingVerificationRule(),
            ]
        else:
            self.rules = rules

    def run(self, ctx: CaseContext) -> list[Finding]:
        all_findings: list[Finding] = []
        for rule in self.rules:
            try:
                results = rule.evaluate(ctx)
                all_findings.extend(results)
            except Exception as e:
                # Fail gracefully on rule failure
                pass
        return all_findings

verification_engine = VerificationEngine()
