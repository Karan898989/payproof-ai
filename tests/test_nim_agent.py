import pytest
from decimal import Decimal
from payproof.domain.models import PaymentCase, Finding
from payproof.domain.enums import CaseState, FindingSeverity, FindingStatus
from payproof.rules.base import CaseContext
from payproof.agents.payment_agent import PaymentVerificationAgent
from payproof.agents.nim_client import NimClient

import asyncio

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
