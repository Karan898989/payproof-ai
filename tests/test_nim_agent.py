import os
import json
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock
import pytest

from payproof.domain.models import PaymentCase, Finding
from payproof.domain.enums import CaseState, FindingSeverity, FindingStatus
from payproof.rules.base import CaseContext
from payproof.agents.payment_agent import PaymentVerificationAgent, _extract_json
from payproof.agents.nim_client import NimClient

def test_agent_fallback_mode():
    async def _run():
        unconfigured_client = NimClient(api_key="")
        agent = PaymentVerificationAgent(client=unconfigured_client)

        case = PaymentCase(
            case_number="CAS-TEST",
            amount=Decimal("1000.00"),
            currency="USD",
            state=CaseState.DRAFT
        )
        ctx = CaseContext(case=case, evidence=[], fields=[])
        findings = [
            Finding(
                case_id=case.id,
                rule_id="BENEFICIARY_001_NEW_ACCOUNT",
                severity=FindingSeverity.CRITICAL,
                status=FindingStatus.FAIL,
                title="New Account",
                explanation="Unverified bank account",
                evidence_ids=[]
            )
        ]

        res = await agent.analyze_case(ctx, findings)
        assert res["success"] is False
        assert res["model"] == "deterministic_fallback"
        assert "critical discrepancies" in res["summary"]
        assert res["intent"]["requests_payment_detail_change"] is True

    asyncio.run(_run())

def test_nim_client_configuration_resolution():
    # 1. Unconfigured
    client = NimClient(api_key="")
    # Clear env var if present for isolation
    old_env = os.environ.pop("NVIDIA_API_KEY", None)
    try:
        assert client.is_configured() is False

        # 2. Configured via instance
        client.api_key = "nvapi-test-key-123456789"
        assert client.is_configured() is True
        assert client.api_key == "nvapi-test-key-123456789"

        # 3. Configured via environment variable
        client_env = NimClient(api_key=None)
        os.environ["NVIDIA_API_KEY"] = "nvapi-env-key-987654321"
        assert client_env.is_configured() is True
        assert client_env.api_key == "nvapi-env-key-987654321"
    finally:
        if old_env is not None:
            os.environ["NVIDIA_API_KEY"] = old_env
        else:
            os.environ.pop("NVIDIA_API_KEY", None)

def test_extract_json_resilience():
    # Case 1: Pure JSON
    payload = {
        "intent": {
            "requests_payment_detail_change": True,
            "claimed_new_beneficiary": "99991111",
            "claims_prior_approval": False,
            "claimed_approver": None,
            "urgency_level": "high",
            "supporting_quotes": ["wire funds now"],
            "uncertainties": []
        },
        "contradictions": [],
        "executive_summary": "High risk bank change detected.",
        "confidence": "high"
    }
    assert _extract_json(json.dumps(payload)) == payload

    # Case 2: Markdown code fence
    fenced = f"```json\n{json.dumps(payload)}\n```"
    assert _extract_json(fenced) == payload

    # Case 3: Nemotron 3 Ultra reasoning tokens (<think>...</think>) + conversational preamble
    with_think = f"""<think>
The user is requesting wire details change to account 99991111.
This contradicts the existing vendor master file.
Urgency level is high.
</think>
Here is the structured analysis:
```json
{json.dumps(payload)}
```
Hope this helps!"""
    assert _extract_json(with_think) == payload

def test_agent_nemotron_inference_success():
    async def _run():
        mock_client = NimClient(api_key="nvapi-mock-test-key")
        sample_response = json.dumps({
            "intent": {
                "requests_payment_detail_change": True,
                "claimed_new_beneficiary": "US99BANK0001",
                "claims_prior_approval": False,
                "claimed_approver": None,
                "urgency_level": "critical",
                "supporting_quotes": ["Please wire immediately to our updated account"],
                "uncertainties": []
            },
            "contradictions": [
                {
                    "statement_a": "Invoice lists Chase account 3210",
                    "statement_b": "Email requests payment to Wells Fargo account 0001",
                    "explanation": "Bank account mismatch between email and invoice."
                }
            ],
            "executive_summary": "Urgent request to change payment destination to unverified bank account. Discrepancy detected.",
            "confidence": "high"
        })
        mock_client.generate_chat_completion = AsyncMock(return_value=f"<think>Analyzing discrepancies</think>\n```json\n{sample_response}\n```")

        agent = PaymentVerificationAgent(client=mock_client)
        case = PaymentCase(
            case_number="CAS-NEMOTRON-01",
            amount=Decimal("14500.00"),
            currency="USD",
            state=CaseState.DRAFT
        )
        ctx = CaseContext(case=case, evidence=[], fields=[])
        findings = []

        res = await agent.analyze_case(ctx, findings)
        assert res["success"] is True
        assert res["model"] == "nvidia/nemotron-3-ultra-550b-a55b"
        assert res["confidence"] == "high"
        assert res["intent"]["requests_payment_detail_change"] is True
        assert len(res["contradictions"]) == 1
        assert "Urgent request" in res["summary"]

    asyncio.run(_run())
