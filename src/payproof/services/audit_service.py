import hashlib
import json
from uuid import uuid4
from ..domain.models import AuditEvent, User, utc_now
from ..repositories.case_repo import case_repo

class AuditService:
    def record_event(
        self,
        actor: User,
        event_type: str,
        case_id: str | None = None,
        payload: dict | None = None,
    ) -> AuditEvent:
        last_event = case_repo.get_last_audit_event()
        prev_hash = last_event.event_hash if last_event else None

        safe_payload = payload or {}
        # Mask any sensitive account numbers in payload
        sanitized_payload = self._mask_sensitive(safe_payload)

        timestamp = utc_now()
        event_id = str(uuid4())

        # Compute tamper-evident hash
        hash_data = {
            "id": event_id,
            "case_id": case_id,
            "actor_id": actor.id,
            "actor_role": actor.role.value,
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "payload": sanitized_payload,
            "prev_hash": prev_hash,
        }
        serialized = json.dumps(hash_data, sort_keys=True)
        event_hash = hashlib.sha256(serialized.encode()).hexdigest()

        event = AuditEvent(
            id=event_id,
            case_id=case_id,
            actor_id=actor.username,
            actor_role=actor.role.value,
            event_type=event_type,
            timestamp=timestamp,
            payload_redacted=sanitized_payload,
            previous_event_hash=prev_hash,
            event_hash=event_hash,
        )
        case_repo.save_audit_event(event)
        return event

    def _mask_sensitive(self, d: dict) -> dict:
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = self._mask_sensitive(v)
            elif isinstance(v, str) and ("account" in k.lower() or "iban" in k.lower()):
                result[k] = f"***{v[-4:]}" if len(v) >= 4 else "***"
            elif "api_key" in k.lower() or "secret" in k.lower() or "password" in k.lower():
                result[k] = "[REDACTED]"
            else:
                result[k] = v
        return result

audit_service = AuditService()
