from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from ..domain.enums import CaseState, DecisionState, EvidenceType, FindingSeverity, FindingStatus, RoleName
from ..domain.models import (
    PaymentCase, EvidenceObject, ProvenancedField, Finding, Decision,
    User, VerificationCallbackRecord, utc_now
)
from ..domain.errors import CaseNotFoundError, InvalidStateTransitionError, AuthorizationDeniedError
from ..repositories.case_repo import case_repo
from ..repositories.evidence_store import evidence_store
from ..parsers.pdf_parser import pdf_parser
from ..parsers.eml_parser import eml_parser
from ..parsers.csv_parser import csv_parser
from ..rules.base import CaseContext
from ..services.verification import verification_engine
from ..services.decisioning import decision_engine
from ..services.audit_service import audit_service
from ..agents.payment_agent import payment_agent
from ..authz.cedar_engine import cedar_engine

class CaseService:
    def create_case(
        self,
        actor: User,
        case_number: str,
        vendor_id: str | None = None,
        vendor_name: str | None = None,
        amount: Decimal = Decimal("0.00"),
        currency: str = "USD",
        invoice_reference: str | None = None,
    ) -> PaymentCase:
        if not cedar_engine.is_authorized(actor, "CreateCase"):
            raise AuthorizationDeniedError(f"User '{actor.username}' with role '{actor.role.value}' cannot create cases.")

        case = PaymentCase(
            id=str(uuid4()),
            case_number=case_number,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            invoice_reference=invoice_reference,
            amount=amount,
            currency=currency,
            state=CaseState.DRAFT,
            created_by=actor.username,
        )
        case_repo.create_case(case)
        audit_service.record_event(
            actor=actor,
            event_type="CASE_CREATED",
            case_id=case.id,
            payload={"case_number": case.case_number, "amount": str(case.amount), "currency": case.currency}
        )
        return case

    def ingest_evidence(
        self,
        actor: User,
        case_id: str,
        filename: str,
        content: bytes,
        mime_type: str,
    ) -> EvidenceObject:
        case = case_repo.get_case(case_id)
        if not case:
            raise CaseNotFoundError(f"Case {case_id} not found")

        if not cedar_engine.is_authorized(actor, "UploadEvidence", case):
            raise AuthorizationDeniedError(f"Role '{actor.role.value}' is not authorized to upload evidence.")

        # Determine evidence type
        fn = filename.lower()
        if fn.endswith(".pdf"):
            ev_type = EvidenceType.INVOICE_PDF
        elif fn.endswith(".eml") or fn.endswith(".msg"):
            ev_type = EvidenceType.EMAIL_EML
        elif "vendor" in fn and fn.endswith(".csv"):
            ev_type = EvidenceType.VENDOR_BASELINE_CSV
        elif "po" in fn or "purchase" in fn and fn.endswith(".csv"):
            ev_type = EvidenceType.PURCHASE_ORDER_CSV
        elif "history" in fn and fn.endswith(".csv"):
            ev_type = EvidenceType.PAYMENT_HISTORY_CSV
        else:
            ev_type = EvidenceType.OTHER

        evidence = evidence_store.save_file(case_id, filename, content, mime_type, ev_type)
        case_repo.add_evidence(evidence)

        # Parse & extract normalized fields
        fields_to_add: list[ProvenancedField] = []

        if ev_type == EvidenceType.INVOICE_PDF:
            parsed = pdf_parser.parse(content)
            if parsed.get("invoice_reference"):
                fields_to_add.append(ProvenancedField(
                    case_id=case_id, name="invoice_reference", raw_value=parsed["invoice_reference"],
                    normalized_value=parsed["invoice_reference"].upper().strip(),
                    evidence_id=evidence.id, extraction_method="parser", source_locator="pdf:invoice_ref"
                ))
                if not case.invoice_reference:
                    case.invoice_reference = parsed["invoice_reference"]
            if parsed.get("amount"):
                fields_to_add.append(ProvenancedField(
                    case_id=case_id, name="invoice_amount", raw_value=str(parsed["amount"]),
                    normalized_value=str(parsed["amount"]), evidence_id=evidence.id,
                    extraction_method="parser", source_locator="pdf:total_amount"
                ))
                case.amount = parsed["amount"]
            if parsed.get("currency"):
                case.currency = parsed["currency"]
            if parsed.get("account_number"):
                fields_to_add.append(ProvenancedField(
                    case_id=case_id, name="invoice_account_number", raw_value=parsed["account_number"],
                    normalized_value=parsed["account_number"].replace("-", "").replace(" ", ""),
                    evidence_id=evidence.id, extraction_method="parser", source_locator="pdf:account"
                ))
            if parsed.get("vendor_name_hint") and not case.vendor_name:
                case.vendor_name = parsed["vendor_name_hint"]
            if parsed.get("raw_text"):
                fields_to_add.append(ProvenancedField(
                    case_id=case_id, name="invoice_raw_text", raw_value=parsed["raw_text"][:4000],
                    normalized_value=parsed["raw_text"][:4000], evidence_id=evidence.id,
                    extraction_method="parser", source_locator="pdf:text"
                ))

        elif ev_type == EvidenceType.EMAIL_EML:
            parsed = eml_parser.parse(content)
            if parsed.get("sender_domain"):
                fields_to_add.append(ProvenancedField(
                    case_id=case_id, name="sender_domain", raw_value=parsed["sender_domain"],
                    normalized_value=parsed["sender_domain"].lower().strip(),
                    evidence_id=evidence.id, extraction_method="parser", source_locator="eml:From"
                ))
            if parsed.get("claimed_account"):
                fields_to_add.append(ProvenancedField(
                    case_id=case_id, name="email_claimed_account", raw_value=parsed["claimed_account"],
                    normalized_value=parsed["claimed_account"].replace("-", "").replace(" ", ""),
                    evidence_id=evidence.id, extraction_method="parser", source_locator="eml:body_account"
                ))
            if parsed.get("body"):
                fields_to_add.append(ProvenancedField(
                    case_id=case_id, name="email_body", raw_value=parsed["body"][:4000],
                    normalized_value=parsed["body"][:4000], evidence_id=evidence.id,
                    extraction_method="parser", source_locator="eml:body"
                ))

        elif ev_type == EvidenceType.VENDOR_BASELINE_CSV:
            vendors = csv_parser.parse_vendor_baseline(content.decode("utf-8", errors="ignore"))
            for v in vendors:
                case_repo.save_vendor(v)
            if vendors and not case.vendor_id:
                case.vendor_id = vendors[0].vendor_id
                case.vendor_name = vendors[0].name

        elif ev_type == EvidenceType.PURCHASE_ORDER_CSV:
            pos = csv_parser.parse_purchase_orders(content.decode("utf-8", errors="ignore"))
            for po in pos:
                case_repo.save_po(po)

        elif ev_type == EvidenceType.PAYMENT_HISTORY_CSV:
            records = csv_parser.parse_payment_history(content.decode("utf-8", errors="ignore"))
            case_repo.save_payment_history(records)

        if fields_to_add:
            case_repo.save_normalized_fields(fields_to_add)

        # Update case state to EVIDENCE_READY if still DRAFT
        if case.state == CaseState.DRAFT:
            case.state = CaseState.EVIDENCE_READY
        case_repo.update_case(case)

        audit_service.record_event(
            actor=actor,
            event_type="EVIDENCE_INGESTED",
            case_id=case_id,
            payload={"filename": filename, "type": ev_type.value, "sha256": evidence.sha256}
        )

        return evidence

    async def analyze_case(self, actor: User, case_id: str) -> Decision:
        case = case_repo.get_case(case_id)
        if not case:
            raise CaseNotFoundError(f"Case {case_id} not found")

        if not cedar_engine.is_authorized(actor, "AnalyzeCase", case):
            raise AuthorizationDeniedError(f"Role '{actor.role.value}' is not authorized to analyze cases.")

        case.state = CaseState.ANALYZING
        case_repo.update_case(case)

        # Load context
        evidence = case_repo.list_evidence_for_case(case_id)
        fields = case_repo.get_normalized_fields(case_id)
        vendor = case_repo.get_vendor(case.vendor_id) if case.vendor_id else None
        
        # If vendor is still None, try matching by name or by vendor_id in baseline
        if not vendor and case.vendor_name:
            # Check if any vendor matches name
            pass

        # Try to find matching PO
        po = None
        if case.vendor_id:
            po = case_repo.get_po_by_vendor(case.vendor_id)

        history = case_repo.get_payment_history_for_vendor(case.vendor_id) if case.vendor_id else []
        callback = case_repo.get_verification_callback(case_id)

        ctx = CaseContext(
            case=case,
            evidence=evidence,
            fields=fields,
            vendor=vendor,
            purchase_order=po,
            payment_history=history,
            verification_callback=callback,
        )

        # 1. Deterministic checks
        findings = verification_engine.run(ctx)
        case_repo.save_findings(case_id, findings)

        # 2. Base decision from deterministic engine
        decision = decision_engine.decide(case_id, findings)

        # 3. Bounded AI Semantic Analysis with Nemotron
        ai_res = await payment_agent.analyze_case(ctx, findings)
        decision.ai_summary = ai_res.get("summary")
        decision.ai_confidence = ai_res.get("confidence")
        decision.ai_intent_analysis = ai_res.get("intent")
        decision.ai_contradictions = [c.get("explanation", "") for c in ai_res.get("contradictions", [])]

        case_repo.save_decision(decision)

        # Update case state based on decision
        if decision.state == DecisionState.PAYMENT_HOLD:
            case.state = CaseState.HELD
        elif decision.state == DecisionState.INDEPENDENT_VENDOR_VERIFICATION_REQUIRED:
            case.state = CaseState.AWAITING_VERIFICATION
        elif decision.state == DecisionState.CLEAR_FOR_STANDARD_APPROVAL:
            case.state = CaseState.STANDARD_APPROVAL_ALLOWED
        else:
            case.state = CaseState.REVIEW_READY

        case_repo.update_case(case)

        audit_service.record_event(
            actor=actor,
            event_type="ANALYSIS_COMPLETED",
            case_id=case_id,
            payload={
                "decision": decision.state.value,
                "reasons": decision.reason_codes,
                "findings_count": len(findings),
                "ai_model": ai_res.get("model", "none"),
            }
        )

        return decision

    def record_verification(
        self,
        actor: User,
        case_id: str,
        callback_phone_used: str,
        vendor_contact_spoken: str,
        confirmation_method: str,
        is_confirmed: bool,
        notes: str,
    ) -> VerificationCallbackRecord:
        case = case_repo.get_case(case_id)
        if not case:
            raise CaseNotFoundError(f"Case {case_id} not found")

        if not cedar_engine.is_authorized(actor, "RecordVerification", case):
            raise AuthorizationDeniedError(f"Role '{actor.role.value}' cannot record out-of-band verification.")

        rec = VerificationCallbackRecord(
            id=str(uuid4()),
            case_id=case_id,
            verified_by=actor.username,
            callback_phone_used=callback_phone_used,
            vendor_contact_spoken=vendor_contact_spoken,
            confirmation_method=confirmation_method,
            is_confirmed=is_confirmed,
            notes=notes,
            timestamp=utc_now(),
        )
        case_repo.save_verification_callback(rec)

        audit_service.record_event(
            actor=actor,
            event_type="VERIFICATION_RECORDED",
            case_id=case_id,
            payload={
                "phone": callback_phone_used,
                "contact": vendor_contact_spoken,
                "confirmed": is_confirmed,
                "notes": notes,
            }
        )

        return rec

    def override_hold(
        self,
        actor: User,
        case_id: str,
        override_reason: str,
    ) -> PaymentCase:
        case = case_repo.get_case(case_id)
        if not case:
            raise CaseNotFoundError(f"Case {case_id} not found")

        if not cedar_engine.is_authorized(actor, "OverrideHold", case, context={"override_reason": override_reason}):
            raise AuthorizationDeniedError(
                f"Role '{actor.role.value}' cannot override holds or justification was missing."
            )

        case.state = CaseState.STANDARD_APPROVAL_ALLOWED
        case_repo.update_case(case)

        audit_service.record_event(
            actor=actor,
            event_type="HOLD_OVERRIDDEN",
            case_id=case_id,
            payload={"override_reason": override_reason}
        )

        return case

    def approve_disposition(
        self,
        actor: User,
        case_id: str,
        notes: str = "",
    ) -> PaymentCase:
        case = case_repo.get_case(case_id)
        if not case:
            raise CaseNotFoundError(f"Case {case_id} not found")

        if not cedar_engine.is_authorized(actor, "ApproveDisposition", case):
            raise AuthorizationDeniedError(f"Role '{actor.role.value}' cannot approve final disposition.")

        if case.state not in (CaseState.STANDARD_APPROVAL_ALLOWED, CaseState.REVIEW_READY):
            raise InvalidStateTransitionError(f"Cannot approve disposition while case is in {case.state.value}")

        case.state = CaseState.CLOSED
        case_repo.update_case(case)

        audit_service.record_event(
            actor=actor,
            event_type="DISPOSITION_APPROVED",
            case_id=case_id,
            payload={"notes": notes}
        )

        return case

case_service = CaseService()
