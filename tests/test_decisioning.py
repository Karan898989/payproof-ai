from payproof.domain.models import Finding
from payproof.domain.enums import DecisionState, FindingSeverity, FindingStatus
from payproof.services.decisioning import DecisionEngine

def test_hard_hold_on_lookalike_domain():
    engine = DecisionEngine()
    findings = [
        Finding(
            case_id="c-1",
            rule_id="DOMAIN_002_LOOKALIKE",
            severity=FindingSeverity.CRITICAL,
            status=FindingStatus.FAIL,
            title="Spoof domain",
            explanation="Spoof",
            evidence_ids=[]
        )
    ]
    decision = engine.decide("c-1", findings)
    assert decision.state == DecisionState.PAYMENT_HOLD
    assert "LOOKALIKE_DOMAIN_SPOOFING" in decision.reason_codes

def test_hard_hold_on_new_account_and_unrecognized_domain():
    engine = DecisionEngine()
    findings = [
        Finding(
            case_id="c-2",
            rule_id="BENEFICIARY_001_NEW_ACCOUNT",
            severity=FindingSeverity.CRITICAL,
            status=FindingStatus.FAIL,
            title="New Account",
            explanation="New Account",
            evidence_ids=[]
        ),
        Finding(
            case_id="c-2",
            rule_id="DOMAIN_001_UNRECOGNIZED_SENDER",
            severity=FindingSeverity.HIGH,
            status=FindingStatus.FAIL,
            title="Unknown Domain",
            explanation="Unknown Domain",
            evidence_ids=[]
        )
    ]
    decision = engine.decide("c-2", findings)
    assert decision.state == DecisionState.PAYMENT_HOLD

def test_independent_verification_required_on_ben_change():
    engine = DecisionEngine()
    findings = [
        Finding(
            case_id="c-3",
            rule_id="BENEFICIARY_001_NEW_ACCOUNT",
            severity=FindingSeverity.CRITICAL,
            status=FindingStatus.FAIL,
            title="New Account",
            explanation="New Account",
            evidence_ids=[]
        ),
        Finding(
            case_id="c-3",
            rule_id="DOMAIN_001_UNRECOGNIZED_SENDER",
            severity=FindingSeverity.LOW,
            status=FindingStatus.PASS,
            title="Sender OK",
            explanation="Sender OK",
            evidence_ids=[]
        )
    ]
    decision = engine.decide("c-3", findings)
    assert decision.state == DecisionState.INDEPENDENT_VENDOR_VERIFICATION_REQUIRED

def test_clear_for_standard_approval():
    engine = DecisionEngine()
    findings = [
        Finding(
            case_id="c-4",
            rule_id="BENEFICIARY_001_NEW_ACCOUNT",
            severity=FindingSeverity.LOW,
            status=FindingStatus.PASS,
            title="Account Match",
            explanation="Match",
            evidence_ids=[]
        ),
        Finding(
            case_id="c-4",
            rule_id="DOMAIN_001_UNRECOGNIZED_SENDER",
            severity=FindingSeverity.LOW,
            status=FindingStatus.PASS,
            title="Domain Match",
            explanation="Match",
            evidence_ids=[]
        )
    ]
    decision = engine.decide("c-4", findings)
    assert decision.state == DecisionState.CLEAR_FOR_STANDARD_APPROVAL
