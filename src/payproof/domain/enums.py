from enum import Enum

class CaseState(str, Enum):
    DRAFT = "DRAFT"
    EVIDENCE_READY = "EVIDENCE_READY"
    ANALYZING = "ANALYZING"
    ANALYSIS_PARTIAL = "ANALYSIS_PARTIAL"
    REVIEW_READY = "REVIEW_READY"
    AWAITING_VERIFICATION = "AWAITING_VERIFICATION"
    HELD = "HELD"
    STANDARD_APPROVAL_ALLOWED = "STANDARD_APPROVAL_ALLOWED"
    CLOSED = "CLOSED"

class DecisionState(str, Enum):
    CLEAR_FOR_STANDARD_APPROVAL = "CLEAR_FOR_STANDARD_APPROVAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INDEPENDENT_VENDOR_VERIFICATION_REQUIRED = "INDEPENDENT_VENDOR_VERIFICATION_REQUIRED"
    PAYMENT_HOLD = "PAYMENT_HOLD"

class EvidenceType(str, Enum):
    INVOICE_PDF = "INVOICE_PDF"
    EMAIL_EML = "EMAIL_EML"
    VENDOR_BASELINE_CSV = "VENDOR_BASELINE_CSV"
    PURCHASE_ORDER_CSV = "PURCHASE_ORDER_CSV"
    PAYMENT_HISTORY_CSV = "PAYMENT_HISTORY_CSV"
    VERIFICATION_RECORD = "VERIFICATION_RECORD"
    OTHER = "OTHER"

class FindingSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FindingStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"

class FindingOrigin(str, Enum):
    DETERMINISTIC = "deterministic"
    AI = "ai"

class RoleName(str, Enum):
    ANALYST = "Analyst"
    APPROVER = "Approver"
    AUDITOR = "Auditor"
    ADMIN = "Admin"
