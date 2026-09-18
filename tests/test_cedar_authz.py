from payproof.domain.models import User
from payproof.domain.enums import RoleName
from payproof.authz.cedar_engine import cedar_engine

def test_analyst_permissions():
    analyst = User(username="analyst", full_name="Alex", role=RoleName.ANALYST, email="a@test.local")

    assert cedar_engine.is_authorized(analyst, "CreateCase") is True
    assert cedar_engine.is_authorized(analyst, "UploadEvidence") is True
    assert cedar_engine.is_authorized(analyst, "AnalyzeCase") is True
    assert cedar_engine.is_authorized(analyst, "ReadCase") is True
    assert cedar_engine.is_authorized(analyst, "ExportCase") is True

    # Explicit forbids for Analyst
    assert cedar_engine.is_authorized(analyst, "OverrideHold") is False
    assert cedar_engine.is_authorized(analyst, "ApproveDisposition") is False
    assert cedar_engine.is_authorized(analyst, "RecordVerification") is False

def test_approver_permissions():
    approver = User(username="approver", full_name="Morgan", role=RoleName.APPROVER, email="m@test.local")

    assert cedar_engine.is_authorized(approver, "ReadCase") is True
    assert cedar_engine.is_authorized(approver, "RecordVerification") is True
    assert cedar_engine.is_authorized(approver, "ApproveDisposition") is True

    # Override without reason must be denied
    assert cedar_engine.is_authorized(approver, "OverrideHold", context={}) is False
    assert cedar_engine.is_authorized(approver, "OverrideHold", context={"override_reason": ""}) is False

    # Override with reason must be allowed
    assert cedar_engine.is_authorized(approver, "OverrideHold", context={"override_reason": "Executive approved in board meeting"}) is True

def test_auditor_permissions():
    auditor = User(username="auditor", full_name="Sarah", role=RoleName.AUDITOR, email="s@test.local")

    assert cedar_engine.is_authorized(auditor, "ReadCase") is True
    assert cedar_engine.is_authorized(auditor, "ExportCase") is True

    # Denied all mutation actions
    assert cedar_engine.is_authorized(auditor, "CreateCase") is False
    assert cedar_engine.is_authorized(auditor, "UploadEvidence") is False
    assert cedar_engine.is_authorized(auditor, "AnalyzeCase") is False
    assert cedar_engine.is_authorized(auditor, "RecordVerification") is False
    assert cedar_engine.is_authorized(auditor, "OverrideHold") is False
    assert cedar_engine.is_authorized(auditor, "ApproveDisposition") is False

def test_admin_permissions():
    admin = User(username="admin", full_name="Dev", role=RoleName.ADMIN, email="admin@test.local")
    assert cedar_engine.is_authorized(admin, "CreateCase") is True
    assert cedar_engine.is_authorized(admin, "OverrideHold") is True
    assert cedar_engine.is_authorized(admin, "ManageBaseline") is True
