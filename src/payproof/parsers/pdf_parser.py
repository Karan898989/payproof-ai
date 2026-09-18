import io
import re
from decimal import Decimal
from pypdf import PdfReader

class PDFInvoiceParser:
    """Extracts text and key invoice metadata from text-based PDF files."""

    def parse(self, pdf_bytes: bytes) -> dict:
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            full_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        except Exception as e:
            return {
                "error": f"Failed to parse PDF: {str(e)}",
                "raw_text": "",
                "is_scanned_or_empty": True,
            }

        full_text = full_text.strip()
        if not full_text:
            return {
                "error": "PDF has no extractable text layer (OCR_REQUIRED)",
                "raw_text": "",
                "is_scanned_or_empty": True,
            }

        # Extract invoice reference
        inv_match = re.search(r'(?:invoice\s*(?:number|no|#)?[:\s]*)([A-Z0-9\-_/]+)', full_text, re.IGNORECASE)
        invoice_ref = inv_match.group(1).strip() if inv_match else None

        # Extract amount
        amount_match = re.search(r'(?:total\s*(?:amount|due)?[:\s]*[\$€£]?)\s*([\d,]+\.\d{2})', full_text, re.IGNORECASE)
        if not amount_match:
            amount_match = re.search(r'[\$€£]\s*([\d,]+\.\d{2})', full_text)

        amount = None
        if amount_match:
            try:
                cleaned = amount_match.group(1).replace(",", "")
                amount = Decimal(cleaned)
            except Exception:
                pass

        # Extract currency
        currency = "USD"
        if "€" in full_text or "EUR" in full_text:
            currency = "EUR"
        elif "£" in full_text or "GBP" in full_text:
            currency = "GBP"

        # Extract bank account / IBAN / routing
        account_match = re.search(r'(?:account\s*(?:number|no|#)?[:\s]*)([0-9A-Z\-]{6,24})', full_text, re.IGNORECASE)
        account_number = account_match.group(1).strip() if account_match else None

        routing_match = re.search(r'(?:routing\s*(?:number|no|#)?[:\s]*)([0-9]{9})', full_text, re.IGNORECASE)
        routing_number = routing_match.group(1).strip() if routing_match else None

        iban_match = re.search(r'\b([A-Z]{2}[0-9]{2}[A-Z0-9]{11,30})\b', full_text)
        iban = iban_match.group(1).strip() if iban_match else None

        # Extract vendor name hint
        vendor_match = re.search(r'(?:from|vendor|company)[:\s]*([A-Za-z0-9\s,\.]{3,40})', full_text, re.IGNORECASE)
        vendor_name_hint = vendor_match.group(1).strip() if vendor_match else None

        return {
            "raw_text": full_text,
            "invoice_reference": invoice_ref,
            "amount": amount,
            "currency": currency,
            "account_number": account_number or iban,
            "routing_number": routing_number,
            "vendor_name_hint": vendor_name_hint,
            "is_scanned_or_empty": False,
        }

pdf_parser = PDFInvoiceParser()
