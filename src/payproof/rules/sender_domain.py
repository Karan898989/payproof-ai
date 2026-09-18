from ..domain.enums import FindingOrigin, FindingSeverity, FindingStatus
from ..domain.models import Finding
from .base import CaseContext, VerificationRule

def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

class SenderDomainRule:
    rule_id: str = "DOMAIN_001_UNRECOGNIZED_SENDER"
    version: str = "1.0.0"

    def evaluate(self, ctx: CaseContext) -> list[Finding]:
        sender_domain = ctx.get_field_val("sender_domain")
        ev_id = ctx.get_field_evidence_id("sender_domain")
        ev_ids = [ev_id] if ev_id else []

        if not sender_domain:
            return []

        if not ctx.vendor or not ctx.vendor.trusted_domains:
            return []

        trusted_domains = [d.lower().strip() for d in ctx.vendor.trusted_domains]
        sender_clean = sender_domain.lower().strip()

        if sender_clean in trusted_domains:
            return [
                Finding(
                    case_id=ctx.case.id,
                    rule_id=self.rule_id,
                    severity=FindingSeverity.LOW,
                    status=FindingStatus.PASS,
                    title="Sender Domain Recognized",
                    explanation=f"Sender domain '{sender_clean}' is in trusted domains list for '{ctx.vendor.name}'.",
                    evidence_ids=ev_ids,
                    origin=FindingOrigin.DETERMINISTIC,
                )
            ]
        else:
            return [
                Finding(
                    case_id=ctx.case.id,
                    rule_id=self.rule_id,
                    severity=FindingSeverity.HIGH,
                    status=FindingStatus.FAIL,
                    title="Unrecognized Email Sender Domain",
                    explanation=(
                        f"Sender domain '{sender_clean}' does NOT match any authorized domain for vendor '{ctx.vendor.name}'. "
                        f"Authorized domains are: {', '.join(trusted_domains)}."
                    ),
                    evidence_ids=ev_ids,
                    origin=FindingOrigin.DETERMINISTIC,
                    metadata={"sender_domain": sender_clean, "trusted_domains": trusted_domains}
                )
            ]

class LookalikeDomainRule:
    rule_id: str = "DOMAIN_002_LOOKALIKE"
    version: str = "1.0.0"

    def evaluate(self, ctx: CaseContext) -> list[Finding]:
        sender_domain = ctx.get_field_val("sender_domain")
        ev_id = ctx.get_field_evidence_id("sender_domain")
        ev_ids = [ev_id] if ev_id else []

        if not sender_domain or not ctx.vendor or not ctx.vendor.trusted_domains:
            return []

        trusted_domains = [d.lower().strip() for d in ctx.vendor.trusted_domains]
        sender_clean = sender_domain.lower().strip()

        if sender_clean in trusted_domains:
            return []

        # Check for lookalike / typosquatting
        # 1. Edit distance 1 or 2
        # 2. Common visual substitutions: rn -> m, vv -> w, 0 -> o, 1 -> l
        normalized_sender = (
            sender_clean
            .replace("rn", "m")
            .replace("vv", "w")
            .replace("0", "o")
            .replace("1", "l")
        )

        for td in trusted_domains:
            dist = levenshtein_distance(sender_clean, td)
            # Typosquatting condition
            is_close = 1 <= dist <= 2
            is_subst = (normalized_sender == td) or (sender_clean.replace("-", "") == td.replace("-", ""))

            if is_close or is_subst:
                return [
                    Finding(
                        case_id=ctx.case.id,
                        rule_id=self.rule_id,
                        severity=FindingSeverity.CRITICAL,
                        status=FindingStatus.FAIL,
                        title=f"Suspected Lookalike/Spoofed Domain: '{sender_clean}'",
                        explanation=(
                            f"Email domain '{sender_clean}' closely mimics trusted vendor domain '{td}' "
                            f"(Levenshtein distance: {dist}). This strongly indicates a Business Email Compromise (BEC) impersonation attempt."
                        ),
                        evidence_ids=ev_ids,
                        origin=FindingOrigin.DETERMINISTIC,
                        metadata={"sender_domain": sender_clean, "trusted_domain": td, "distance": dist}
                    )
                ]

        return []
