import csv
import io
import hashlib
from decimal import Decimal
from uuid import uuid4
from ..domain.models import VendorBaseline, VendorAccount, PurchaseOrder, PaymentHistoryRecord

class CSVParser:
    """Parses CSV files for Vendor Baselines, Purchase Orders, and Payment History."""

    def parse_vendor_baseline(self, csv_text: str) -> list[VendorBaseline]:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        vendors_dict: dict[str, VendorBaseline] = {}

        for row in reader:
            vendor_id = row.get("vendor_id", "").strip()
            name = row.get("name", "").strip()
            domain = row.get("domain", "").strip().lower()
            phone = row.get("contact_phone", "").strip()
            contact = row.get("contact_name", "").strip()

            bank_name = row.get("bank_name", "").strip()
            routing = row.get("routing_number", "").strip()
            account_num = row.get("account_number", "").strip()

            if not vendor_id or not name:
                continue

            if vendor_id not in vendors_dict:
                vendors_dict[vendor_id] = VendorBaseline(
                    vendor_id=vendor_id,
                    name=name,
                    trusted_domains=[domain] if domain else [],
                    accounts=[],
                    contact_phone=phone,
                    contact_name=contact,
                )
            else:
                if domain and domain not in vendors_dict[vendor_id].trusted_domains:
                    vendors_dict[vendor_id].trusted_domains.append(domain)

            if bank_name and account_num:
                acc_last4 = account_num[-4:] if len(account_num) >= 4 else account_num
                acc_hash = hashlib.sha256(account_num.encode()).hexdigest()
                account = VendorAccount(
                    id=str(uuid4()),
                    vendor_id=vendor_id,
                    bank_name=bank_name,
                    routing_number=routing,
                    account_number_last4=acc_last4,
                    full_account_hash=acc_hash,
                    status="active",
                )
                vendors_dict[vendor_id].accounts.append(account)

        return list(vendors_dict.values())

    def parse_purchase_orders(self, csv_text: str) -> list[PurchaseOrder]:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        pos = []
        for row in reader:
            po_num = row.get("po_number", "").strip()
            vendor_id = row.get("vendor_id", "").strip()
            vendor_name = row.get("vendor_name", "").strip()
            amount_str = row.get("amount", "0").replace("$", "").replace(",", "").strip()
            currency = row.get("currency", "USD").strip().upper()
            status = row.get("status", "approved").strip().lower()

            if po_num and vendor_id:
                pos.append(
                    PurchaseOrder(
                        po_number=po_num,
                        vendor_id=vendor_id,
                        vendor_name=vendor_name,
                        amount=Decimal(amount_str or "0"),
                        currency=currency,
                        status="approved" if "app" in status else "partially_fulfilled",
                    )
                )
        return pos

    def parse_payment_history(self, csv_text: str) -> list[PaymentHistoryRecord]:
        reader = csv.DictReader(io.StringIO(csv_text.strip()))
        records = []
        for row in reader:
            payment_id = row.get("payment_id", str(uuid4())).strip()
            vendor_id = row.get("vendor_id", "").strip()
            amount_str = row.get("amount", "0").replace("$", "").replace(",", "").strip()
            currency = row.get("currency", "USD").strip().upper()
            paid_date = row.get("paid_date", "").strip()
            invoice_ref = row.get("invoice_ref", "").strip()
            status = row.get("status", "completed").strip().lower()

            if vendor_id:
                records.append(
                    PaymentHistoryRecord(
                        payment_id=payment_id,
                        vendor_id=vendor_id,
                        amount=Decimal(amount_str or "0"),
                        currency=currency,
                        paid_date=paid_date,
                        invoice_ref=invoice_ref,
                        status="completed" if "comp" in status else "reversed",
                    )
                )
        return records

csv_parser = CSVParser()
