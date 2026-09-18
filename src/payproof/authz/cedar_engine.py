from ..domain.enums import RoleName
from ..domain.models import User, PaymentCase
from .port import AuthorizationPort

class CedarEngine(AuthorizationPort):
    """Native implementation of Cedar policies for PayProof AI."""

    def is_authorized(
        self,
        user: User,
        action: str,
        resource: PaymentCase | None = None,
        context: dict | None = None,
    ) -> bool:
        role = user.role

        # Admin: permit all
        if role == RoleName.ADMIN:
            return True

        # Auditor: read-only access (ReadCase, ExportCase)
        if role == RoleName.AUDITOR:
            if action in ("ReadCase", "ExportCase"):
                return True
            return False  # Strict read-only, all mutations denied

        # Analyst: create, read, upload, analyze, request verification, export
        if role == RoleName.ANALYST:
            # Explicit forbid:
            if action in ("OverrideHold", "ApproveDisposition", "RecordVerification", "ManageBaseline"):
                return False
            if action in ("CreateCase", "ReadCase", "UploadEvidence", "AnalyzeCase", "RequestVerification", "ExportCase"):
                return True
            return False

        # Approver: read, analyze, request/record verification, approve disposition, override hold with reason
        if role == RoleName.APPROVER:
            if action in ("ReadCase", "AnalyzeCase", "RequestVerification", "RecordVerification", "ApproveDisposition", "OverrideHold", "ExportCase"):
                # If overriding hold, context must contain justification
                if action == "OverrideHold":
                    if not context or not context.get("override_reason"):
                        return False
                return True
            return False

        # Default deny
        return False

cedar_engine = CedarEngine()
