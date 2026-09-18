import pytest
from decimal import Decimal
import hashlib
from payproof.domain.models import (
    PaymentCase, VendorBaseline, VendorAccount, PurchaseOrder, PaymentHistoryRecord,
    ProvenancedField, VerificationCallbackRecord
)
from payproof.domain.enums import CaseState, FindingStatus, FindingSeverity
from payproof.rules.base import CaseContext
from payproof.rules.beneficiary import BeneficiaryChangeRule
from payproof.rules.sender_domain import SenderDomainRule, LookalikeDomainRule
from payproof.rules.duplicate import DuplicateInvoiceRule
from payproof.rules.po_match import POMatchRule
from payproof.rules.amount import AmountHistoryRule
from payproof.rules.missing_ev import MissingBaselineRule, MissingVerificationRule

@pytest.fixture
def sample_vendor():
    acc_hash = hashlib.sha256("1234567890".encode()).hexdigest()
    return VendorBaseline(
        vendor_id="V-001",
        name="Trusted Vendor Corp",
        trusted_domains=["trusted.com"],
        accounts=[
            VendorAccount(
                vendor_id="V-001",
                bank_name="Test Bank",
                routing_number="111000025",
                account_number_last4="7890",
                full_account_hash=acc_hash,
                status="active"
            )
        ],
        contact_phone="+1-555-0100",
        contact_name="Alice Smith"
    )

@pytest.fixture
def sample_case():
    return PaymentCase(
        case_number="CAS-TEST-01",
        vendor_id="V-001",
        vendor_name="Trusted Vendor Corp",
        invoice_reference="INV-100",
        amount=Decimal("5000.00"),
        currency="USD",
        state=CaseState.DRAFT,
    )

def test_beneficiary_rule_known_account(sample_case, sample_vendor):
    fields = [
        ProvenancedField(case_id=sample_case.id, name="invoice_account_number", raw_value="1234567890", normalized_value="1234567890")
    ]
    ctx = CaseContext(case=sample_case, evidence=[], fields=fields, vendor=sample_vendor)
    rule = BeneficiaryChangeRule()
    findings = rule.evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].status == FindingStatus.PASS

def test_beneficiary_rule_new_account(sample_case, sample_vendor):
    fields = [
        ProvenancedField(case_id=sample_case.id, name="email_claimed_account", raw_value="9999999999", normalized_value="9999999999")
    ]
    ctx = CaseContext(case=sample_case, evidence=[], fields=fields, vendor=sample_vendor)
    rule = BeneficiaryChangeRule()
    findings = rule.evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].status == FindingStatus.FAIL
    assert findings[0].severity == FindingSeverity.CRITICAL

def test_sender_domain_exact_match(sample_case, sample_vendor):
    fields = [
        ProvenancedField(case_id=sample_case.id, name="sender_domain", raw_value="trusted.com", normalized_value="trusted.com")
    ]
    ctx = CaseContext(case=sample_case, evidence=[], fields=fields, vendor=sample_vendor)
    rule = SenderDomainRule()
    findings = rule.evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].status == FindingStatus.PASS

def test_sender_domain_unrecognized(sample_case, sample_vendor):
    fields = [
        ProvenancedField(case_id=sample_case.id, name="sender_domain", raw_value="unknown-domain.com", normalized_value="unknown-domain.com")
    ]
    ctx = CaseContext(case=sample_case, evidence=[], fields=fields, vendor=sample_vendor)
    rule = SenderDomainRule()
    findings = rule.evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].status == FindingStatus.FAIL

def test_lookalike_domain_detects_spoof(sample_case, sample_vendor):
    # Typo: trusted.co vs trusted.com
    fields = [
        ProvenancedField(case_id=sample_case.id, name="sender_domain", raw_value="trusted.co", normalized_value="trusted.co")
    ]
    ctx = CaseContext(case=sample_case, evidence=[], fields=fields, vendor=sample_vendor)
    rule = LookalikeDomainRule()
    findings = rule.evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].status == FindingStatus.FAIL
    assert findings[0].severity == FindingSeverity.CRITICAL

def test_duplicate_invoice_rule(sample_case):
    history = [
        PaymentHistoryRecord(payment_id="P-1", vendor_id="V-001", amount=Decimal("5000.00"), currency="USD", paid_date="2026-01-01", invoice_ref="INV-100")
    ]
    ctx = CaseContext(case=sample_case, evidence=[], fields=[], payment_history=history)
    rule = DuplicateInvoiceRule()
    findings = rule.evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].status == FindingStatus.FAIL

def test_po_match_rule(sample_case):
    # PO amount 4000 < Case amount 5000 -> Mismatch
    po = PurchaseOrder(po_number="PO-01", vendor_id="V-001", vendor_name="Vendor", amount=Decimal("4000.00"), currency="USD")
    ctx = CaseContext(case=sample_case, evidence=[], fields=[], purchase_order=po)
    rule = POMatchRule()
    findings = rule.evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].status == FindingStatus.FAIL

def test_amount_outlier_rule(sample_case):
    # History around 1000, case is 5000 -> Outlier
    history = [
        PaymentHistoryRecord(payment_id=f"P-{i}", vendor_id="V-001", amount=Decimal("1000.00"), currency="USD", paid_date=f"2026-0{i}-01", invoice_ref=f"INV-{i}")
        for i in range(1, 5)
    ]
    ctx = CaseContext(case=sample_case, evidence=[], fields=[], payment_history=history)
    rule = AmountHistoryRule()
    findings = rule.evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].status == FindingStatus.FAIL

def test_missing_verification_rule_when_unconfirmed(sample_case, sample_vendor):
    fields = [
        ProvenancedField(case_id=sample_case.id, name="email_claimed_account", raw_value="9999999999", normalized_value="9999999999")
    ]
    ctx = CaseContext(case=sample_case, evidence=[], fields=fields, vendor=sample_vendor, verification_callback=None)
    rule = MissingVerificationRule()
    findings = rule.evaluate(ctx)

    assert len(findings) == 1
    assert findings[0].status == FindingStatus.FAIL
