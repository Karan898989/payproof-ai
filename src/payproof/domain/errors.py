class PayProofError(Exception):
    """Base domain exception."""

class CaseNotFoundError(PayProofError):
    """Case was not found."""

class EvidenceNotFoundError(PayProofError):
    """Evidence was not found."""

class InvalidStateTransitionError(PayProofError):
    """State transition is invalid."""

class AuthorizationDeniedError(PayProofError):
    """User lacks authorization under Cedar policies."""

class ParsingError(PayProofError):
    """Document parsing failed."""
