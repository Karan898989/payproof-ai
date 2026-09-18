from decimal import Decimal
from payproof.parsers.eml_parser import eml_parser
from payproof.parsers.csv_parser import csv_parser
from payproof.parsers.pdf_parser import pdf_parser

def test_eml_parser():
    sample_eml = b"""From: billing@testvendor.com
To: ap@company.com
Subject: New Bank Info
Date: Mon, 15 Sep 2026 12:00:00 +0000

Hello, please update our bank account to 1234567890.
"""
    res = eml_parser.parse(sample_eml)
    assert res["sender_domain"] == "testvendor.com"
    assert res["claimed_account"] == "1234567890"
    assert "update our bank" in res["body"]

def test_csv_parser_vendor_baseline():
    csv_text = """vendor_id,name,domain,contact_phone,contact_name,bank_name,routing_number,account_number
V-1,Alpha Corp,alphacorp.com,+1-555-0199,Alice,JPMorgan,021000021,9876543210
"""
    vendors = csv_parser.parse_vendor_baseline(csv_text)
    assert len(vendors) == 1
    assert vendors[0].vendor_id == "V-1"
    assert vendors[0].trusted_domains == ["alphacorp.com"]
    assert len(vendors[0].accounts) == 1
    assert vendors[0].accounts[0].account_number_last4 == "3210"

def test_csv_parser_purchase_orders():
    csv_text = """po_number,vendor_id,vendor_name,amount,currency,status
PO-100,V-1,Alpha Corp,15000.00,USD,approved
"""
    pos = csv_parser.parse_purchase_orders(csv_text)
    assert len(pos) == 1
    assert pos[0].po_number == "PO-100"
    assert pos[0].amount == Decimal("15000.00")

def test_pdf_parser_empty_or_scanned():
    res = pdf_parser.parse(b"")
    assert res["is_scanned_or_empty"] is True
