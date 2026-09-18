import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from payproof.main import app
from payproof.repositories.db import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()

def test_health_endpoints():
    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    res = client.get("/health/ready")
    assert res.status_code == 200
    assert res.json()["database"] is True

def test_html_views():
    # Test dashboard HTML render
    res = client.get("/")
    assert res.status_code == 200
    assert "PayProof" in res.text
    assert "Pre-Payment Verification Cases" in res.text

    # Test case detail HTML render
    cases = client.get("/api/v1/cases").json()
    if cases:
        case_id = cases[0]["id"]
        res = client.get(f"/cases/{case_id}")
        assert res.status_code == 200
        assert "Review Studio" in res.text or "Dossier" in res.text

import uuid

def test_full_case_lifecycle():
    case_num = f"E2E-{uuid.uuid4().hex[:8].upper()}"
    # 1. Create Case as Analyst
    res = client.post(
        "/api/v1/cases",
        headers={"X-PayProof-User": "analyst"},
        json={
            "case_number": case_num,
            "amount": 2500.00,
            "currency": "USD",
            "invoice_reference": "INV-E2E-1"
        }
    )
    assert res.status_code == 200
    case_data = res.json()
    case_id = case_data["id"]

    # 2. Upload Email Evidence
    eml_content = b"""From: billing@unknown-vendor.com
To: ap@test.com
Subject: Pay to new account 9999888877

Please wire funds now.
"""
    res = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        headers={"X-PayProof-User": "analyst"},
        files={"file": ("email.eml", eml_content, "message/rfc822")}
    )
    assert res.status_code == 200

    # 3. Analyze Case
    res = client.post(
        f"/api/v1/cases/{case_id}/analyze",
        headers={"X-PayProof-User": "analyst"}
    )
    assert res.status_code == 200
    analysis = res.json()
    assert "decision" in analysis
    assert "findings" in analysis

    # 4. Analyst tries to override hold -> Denied by Cedar
    res = client.post(
        f"/api/v1/cases/{case_id}/override",
        headers={"X-PayProof-User": "analyst"},
        json={"override_reason": "I am an analyst trying to bypass"}
    )
    assert res.status_code == 403

    # 5. Approver overrides hold -> Allowed by Cedar
    res = client.post(
        f"/api/v1/cases/{case_id}/override",
        headers={"X-PayProof-User": "approver"},
        json={"override_reason": "CFO signed off on emergency exception"}
    )
    assert res.status_code == 200
    assert res.json()["state"] == "STANDARD_APPROVAL_ALLOWED"

    # 6. Approver approves final disposition -> Closed
    res = client.post(
        f"/api/v1/cases/{case_id}/disposition",
        headers={"X-PayProof-User": "approver"},
        json={"notes": "Final release approved"}
    )
    assert res.status_code == 200
    assert res.json()["state"] == "CLOSED"

    # 7. Verify Audit Trail and Export Dossier
    res = client.get(
        f"/api/v1/cases/{case_id}/export",
        headers={"X-PayProof-User": "auditor"}
    )
    assert res.status_code == 200
    dossier = res.json()
    assert dossier["manifest"]["audit_chain_integrity"] == "VALID"
    assert len(dossier["audit_trail"]) >= 4
