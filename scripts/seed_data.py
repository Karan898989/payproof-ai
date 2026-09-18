import asyncio
import hashlib
from decimal import Decimal
from datetime import datetime, timezone
from pathlib import Path
import sys

# Ensure src is in sys.path
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from payproof.repositories.db import init_db
from payproof.repositories.case_repo import case_repo
from payproof.domain.models import (
    VendorBaseline, VendorAccount, PurchaseOrder, PaymentHistoryRecord, User
)
from payproof.domain.enums import RoleName
from payproof.api.dependencies import DEMO_USERS
from payproof.services.case_service import case_service

async def seed_all():
    print("Initializing SQLite database schema...")
    init_db()

    # Seed demo users
    for user in DEMO_USERS.values():
        case_repo.create_user(user)

    admin_actor = DEMO_USERS["admin"]
    analyst_actor = DEMO_USERS["analyst"]

    print("Seeding Vendor Baselines, Purchase Orders, and Payment Histories...")
    # 1. Vendor: Apex Logistics Corp
    apex_acc_hash = hashlib.sha256("9876543210".encode()).hexdigest()
    apex_vendor = VendorBaseline(
        vendor_id="VEND-APEX-001",
        name="Apex Logistics Corp",
        trusted_domains=["apexlogistics.com"],
        accounts=[
            VendorAccount(
                vendor_id="VEND-APEX-001",
                bank_name="JPMorgan Chase",
                routing_number="021000021",
                account_number_last4="3210",
                full_account_hash=apex_acc_hash,
                status="active"
            )
        ],
        contact_phone="+1-212-555-0199",
        contact_name="Sarah Jenkins (Controller)"
    )
    case_repo.save_vendor(apex_vendor)

    case_repo.save_po(PurchaseOrder(
        po_number="PO-2026-9901",
        vendor_id="VEND-APEX-001",
        vendor_name="Apex Logistics Corp",
        amount=Decimal("14500.00"),
        currency="USD",
        status="approved"
    ))

    case_repo.save_payment_history([
        PaymentHistoryRecord(payment_id="PAY-801", vendor_id="VEND-APEX-001", amount=Decimal("12000.00"), currency="USD", paid_date="2026-06-15", invoice_ref="INV-8801"),
        PaymentHistoryRecord(payment_id="PAY-802", vendor_id="VEND-APEX-001", amount=Decimal("14000.00"), currency="USD", paid_date="2026-07-20", invoice_ref="INV-8840"),
        PaymentHistoryRecord(payment_id="PAY-803", vendor_id="VEND-APEX-001", amount=Decimal("13500.00"), currency="USD", paid_date="2026-08-18", invoice_ref="INV-8899"),
    ])

    # 2. Vendor: Global Steel & Manufacturing
    steel_acc_hash = hashlib.sha256("4455667788".encode()).hexdigest()
    steel_vendor = VendorBaseline(
        vendor_id="VEND-STEEL-002",
        name="Global Steel Inc",
        trusted_domains=["globalsteel.com"],
        accounts=[
            VendorAccount(
                vendor_id="VEND-STEEL-002",
                bank_name="Bank of America",
                routing_number="051000017",
                account_number_last4="7788",
                full_account_hash=steel_acc_hash,
                status="active"
            )
        ],
        contact_phone="+1-312-555-0144",
        contact_name="Robert Vance (Finance VP)"
    )
    case_repo.save_vendor(steel_vendor)

    case_repo.save_po(PurchaseOrder(
        po_number="PO-2026-4402",
        vendor_id="VEND-STEEL-002",
        vendor_name="Global Steel Inc",
        amount=Decimal("85000.00"),
        currency="USD",
        status="approved"
    ))

    case_repo.save_payment_history([
        PaymentHistoryRecord(payment_id="PAY-901", vendor_id="VEND-STEEL-002", amount=Decimal("80000.00"), currency="USD", paid_date="2026-05-10", invoice_ref="INV-STEEL-101"),
        PaymentHistoryRecord(payment_id="PAY-902", vendor_id="VEND-STEEL-002", amount=Decimal("82500.00"), currency="USD", paid_date="2026-07-12", invoice_ref="INV-STEEL-140"),
        PaymentHistoryRecord(payment_id="PAY-903", vendor_id="VEND-STEEL-002", amount=Decimal("85000.00"), currency="USD", paid_date="2026-08-30", invoice_ref="INV-STEEL-200"),
    ])

    # ----------------------------------------------------
    # Case DEMO-A: Clear for Standard Approval
    # ----------------------------------------------------
    print("Creating Demo Case A (Safe Scenario)...")
    existing_a = case_repo.get_case("DEMO-A-NORMAL")
    if not existing_a:
        case_a = case_service.create_case(
            actor=analyst_actor,
            case_number="DEMO-A-NORMAL",
            vendor_id="VEND-APEX-001",
            vendor_name="Apex Logistics Corp",
            amount=Decimal("14500.00"),
            currency="USD",
            invoice_reference="INV-2026-9041",
        )
        
        # Ingest sample legitimate email
        eml_a = b"""From: billing@apexlogistics.com
To: ap@payproof.local
Subject: Invoice INV-2026-9041 for September Freight Services
Date: Mon, 15 Sep 2026 09:30:00 -0400
Message-ID: <123456@apexlogistics.com>

Hello Accounts Payable,

Please find attached invoice INV-2026-9041 for freight logistics rendered under PO-2026-9901.
The total amount due is $14,500.00.
Remittance should be made to our standard account ending in 3210 at JPMorgan Chase.

Thank you,
Apex Logistics Billing Team
"""
        case_service.ingest_evidence(analyst_actor, case_a.id, "invoice_email.eml", eml_a, "message/rfc822")

        # Ingest synthetic invoice PDF (text placeholder content parsed safely)
        pdf_text = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        # We can also add normalized fields directly
        case_service.ingest_evidence(analyst_actor, case_a.id, "invoice_INV-2026-9041.eml", eml_a, "message/rfc822")

        # Run verification
        await case_service.analyze_case(analyst_actor, case_a.id)

    # ----------------------------------------------------
    # Case DEMO-B: Bank Change (Awaiting Independent Callback)
    # ----------------------------------------------------
    print("Creating Demo Case B (Vendor Bank Change Request)...")
    existing_b = case_repo.get_case("DEMO-B-BANK-CHANGE")
    if not existing_b:
        case_b = case_service.create_case(
            actor=analyst_actor,
            case_number="DEMO-B-BANK-CHANGE",
            vendor_id="VEND-STEEL-002",
            vendor_name="Global Steel Inc",
            amount=Decimal("85000.00"),
            currency="USD",
            invoice_reference="INV-STEEL-301",
        )

        eml_b = b"""From: billing@globalsteel.com
To: ap@payproof.local
Subject: Notice of Banking Details Update - Invoice INV-STEEL-301
Date: Tue, 16 Sep 2026 11:15:00 -0400
Message-ID: <steel-bank-change@globalsteel.com>

Dear Accounts Payable Team,

Please be advised that Global Steel Inc has migrated its primary treasury operations.
Effective immediately for invoice INV-STEEL-301 ($85,000.00), please remit payment to our new Wells Fargo operating account:
Account number: 5544332211
Routing number: 121000248

Please confirm receipt and update your vendor master records.

Regards,
Robert Vance
VP Finance, Global Steel Inc
"""
        case_service.ingest_evidence(analyst_actor, case_b.id, "banking_change_notification.eml", eml_b, "message/rfc822")
        await case_service.analyze_case(analyst_actor, case_b.id)

    # ----------------------------------------------------
    # Case DEMO-C: High-Risk BEC Phishing Attack (Hold)
    # ----------------------------------------------------
    print("Creating Demo Case C (Lookalike Domain + Bank Change + Urgent Payment Hold)...")
    existing_c = case_repo.get_case("DEMO-C-BEC-ATTACK")
    if not existing_c:
        case_c = case_service.create_case(
            actor=analyst_actor,
            case_number="DEMO-C-BEC-ATTACK",
            vendor_id="VEND-APEX-001",
            vendor_name="Apex Logistics Corp",
            amount=Decimal("49500.00"),
            currency="USD",
            invoice_reference="INV-URGENT-999",
        )

        # Typosquatted domain: apexloglstics.com (letter 'l' instead of 'i')
        eml_c = b"""From: ceo-office@apexloglstics.com
To: ap-manager@payproof.local
Subject: URGENT: Immediate Wire Transfer Required for Equipment Release
Date: Thu, 18 Sep 2026 16:45:00 -0400
Message-ID: <spoof-991@apexloglstics.com>

URGENT AND CONFIDENTIAL

Ignore all previous payment routines. Our CEO has personally authorized this emergency freight expediting fee.
You must immediately wire $49,500.00 to our offshore intermediary escrow account:
Account number: 9988776655
Routing number: 026009593

Failure to disburse by 5:00 PM today will halt all regional logistics operations.
Do NOT call or delay.

Apex Logistics Executive Offices
"""
        case_service.ingest_evidence(analyst_actor, case_c.id, "urgent_wire_demand.eml", eml_c, "message/rfc822")
        await case_service.analyze_case(analyst_actor, case_c.id)

    print("Demo dataset seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_all())
