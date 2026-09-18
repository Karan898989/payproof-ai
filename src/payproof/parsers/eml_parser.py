import email
from email import policy
import re
from typing import Any

class EMLParser:
    """Parses email (.eml) files preserving header provenance and extracting body text."""

    def parse(self, eml_bytes: bytes) -> dict[str, Any]:
        try:
            msg = email.message_from_bytes(eml_bytes, policy=policy.default)
        except Exception as e:
            return {
                "error": f"Failed to parse EML: {str(e)}",
                "raw_text": "",
            }

        sender = msg.get("From", "")
        reply_to = msg.get("Reply-To", "")
        to = msg.get("To", "")
        subject = msg.get("Subject", "")
        date = msg.get("Date", "")
        message_id = msg.get("Message-ID", "")

        # Extract sender email and domain
        sender_email = ""
        sender_domain = ""
        match = re.search(r'<([^>]+)>', sender)
        if match:
            sender_email = match.group(1).lower().strip()
        elif "@" in sender:
            sender_email = sender.strip().split()[-1].replace("<", "").replace(">", "").lower()

        if "@" in sender_email:
            sender_domain = sender_email.split("@")[1].lower().strip()

        # Extract plain text body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get("Content-Disposition"))
                if ctype == "text/plain" and "attachment" not in cdispo:
                    try:
                        body += part.get_content() + "\n"
                    except Exception:
                        pass
            if not body: # Fallback to html stripped if no text/plain
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        try:
                            html_text = part.get_content()
                            body = re.sub(r'<[^>]+>', ' ', html_text)
                        except Exception:
                            pass
        else:
            try:
                body = msg.get_content()
            except Exception:
                body = str(msg.get_payload())

        body = body.strip()

        # Extract mentioned accounts in email
        acc_match = re.search(r'(?:account\s*(?:number|no|#|to|is|details)?[:\s]*)([0-9A-Z\-]{6,24})', body, re.IGNORECASE)
        claimed_account = acc_match.group(1).strip().rstrip(".") if acc_match else None

        rout_match = re.search(r'(?:routing\s*(?:number|no|#|is)?[:\s]*)([0-9]{9})', body, re.IGNORECASE)
        claimed_routing = rout_match.group(1).strip().rstrip(".") if rout_match else None

        return {
            "from": sender,
            "sender_email": sender_email,
            "sender_domain": sender_domain,
            "reply_to": reply_to,
            "to": to,
            "subject": subject,
            "date": date,
            "message_id": message_id,
            "body": body,
            "claimed_account": claimed_account,
            "claimed_routing": claimed_routing,
        }

eml_parser = EMLParser()
