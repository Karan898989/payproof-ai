import hashlib
import json
from ..domain.models import PaymentCase
from ..repositories.case_repo import case_repo

class ExportService:
    def export_case_dossier(self, case_id: str) -> dict:
        case = case_repo.get_case(case_id)
        if not case:
            return {}

        evidence = case_repo.list_evidence_for_case(case_id)
        fields = case_repo.get_normalized_fields(case_id)
        findings = case_repo.get_findings_for_case(case_id)
        decision = case_repo.get_decision_for_case(case_id)
        audit_events = case_repo.list_audit_events_for_case(case_id)
        callback = case_repo.get_verification_callback(case_id)

        # Verify audit hash integrity
        audit_chain_valid = True
        for i in range(1, len(audit_events)):
            if audit_events[i].previous_event_hash != audit_events[i-1].event_hash:
                audit_chain_valid = False
                break

        dossier = {
            "manifest": {
                "system": "PayProof AI",
                "version": "0.1.0",
                "exported_at": case.updated_at.isoformat(),
                "case_id": case.id,
                "case_number": case.case_number,
                "audit_chain_integrity": "VALID" if audit_chain_valid else "INVALID",
            },
            "case": case.model_dump(mode="json"),
            "evidence_objects": [
                {
                    "id": e.id,
                    "filename": e.original_filename,
                    "mime_type": e.mime_type,
                    "type": e.evidence_type.value,
                    "sha256": e.sha256,
                    "byte_size": e.byte_size,
                    "ingested_at": e.ingested_at.isoformat(),
                }
                for e in evidence
            ],
            "normalized_fields": [f.model_dump(mode="json") for f in fields],
            "findings": [f.model_dump(mode="json") for f in findings],
            "decision": decision.model_dump(mode="json") if decision else None,
            "verification_callback": callback.model_dump(mode="json") if callback else None,
            "audit_trail": [
                {
                    "id": a.id,
                    "actor": a.actor_id,
                    "role": a.actor_role,
                    "event_type": a.event_type,
                    "timestamp": a.timestamp.isoformat(),
                    "payload": a.payload_redacted,
                    "prev_hash": a.previous_event_hash,
                    "hash": a.event_hash,
                }
                for a in audit_events
            ]
        }

        # Calculate master dossier hash
        dossier_hash = hashlib.sha256(json.dumps(dossier, sort_keys=True).encode()).hexdigest()
        dossier["manifest"]["dossier_sha256"] = dossier_hash

        return dossier

export_service = ExportService()
