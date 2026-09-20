import json
import re
import logging
from typing import Any
from .nim_client import NimClient, nim_client
from .prompts import SYSTEM_SEMANTIC_PROMPT, SEMANTIC_ANALYSIS_PROMPT
from .schemas import SemanticAnalysisResult, PaymentChangeIntent
from ..domain.models import PaymentCase, Finding
from ..rules.base import CaseContext

logger = logging.getLogger("payproof.agent")

def _extract_json(raw: str) -> dict:
    """Extracts and parses JSON object from LLM response, handling thinking tokens, markdown fences, and preambles."""
    # 1. Remove reasoning / <think> blocks if present
    cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # 2. Extract markdown code block if present
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.DOTALL)
    if fence_match:
        return json.loads(fence_match.group(1))

    # 3. Try direct JSON parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 4. Search for root JSON structure { ... }
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return json.loads(cleaned[start_idx : end_idx + 1])

    raise ValueError("No valid JSON object found in response")

class PaymentVerificationAgent:
    def __init__(self, client: NimClient | None = None):
        self.client = client or nim_client

    async def analyze_case(self, ctx: CaseContext, deterministic_findings: list[Finding]) -> dict[str, Any]:
        """Runs NVIDIA Nemotron analysis on case text evidence, or degrades safely."""
        # 1. Gather text snippets
        email_body = ctx.get_field_val("email_body") or "(No email text attached)"
        inv_text = ctx.get_field_val("invoice_raw_text") or "(No invoice text extracted)"

        # Prepare summary of deterministic findings
        findings_summary = "\n".join(
            f"- [{f.severity.value.upper()}] {f.title}: {f.explanation}"
            for f in deterministic_findings
        ) or "None"

        # Check if NIM is available
        if not self.client.is_configured():
            return self._fallback_deterministic_summary(ctx, deterministic_findings, "NVIDIA NIM API key not configured")

        user_prompt = SEMANTIC_ANALYSIS_PROMPT.format(
            case_number=ctx.case.case_number,
            vendor_name=ctx.case.vendor_name or "Unknown",
            amount=str(ctx.case.amount),
            currency=ctx.case.currency,
            deterministic_findings=findings_summary,
            email_text=email_body[:2500],
            invoice_text=inv_text[:2500],
        )

        raw_response = await self.client.generate_chat_completion(SYSTEM_SEMANTIC_PROMPT, user_prompt)
        if not raw_response:
            return self._fallback_deterministic_summary(ctx, deterministic_findings, "NIM inference unavailable or timed out")

        # Parse JSON
        try:
            data = _extract_json(raw_response)
            result = SemanticAnalysisResult(**data)
            return {
                "success": True,
                "model": self.client.model,
                "summary": result.executive_summary,
                "confidence": result.confidence,
                "intent": result.intent.model_dump(),
                "contradictions": [c.model_dump() for c in result.contradictions],
            }
        except Exception as e:
            logger.warning("Failed to parse Nemotron structured output: %s", str(e))
            return self._fallback_deterministic_summary(ctx, deterministic_findings, f"Nemotron response schema mismatch: {str(e)}")

    def _fallback_deterministic_summary(self, ctx: CaseContext, findings: list[Finding], reason: str) -> dict[str, Any]:
        """Graceful fallback synthesized from deterministic findings."""
        failed = [f for f in findings if f.status.value == "fail"]
        if failed:
            summary = (
                f"Automated verification flagged {len(failed)} critical discrepancies. "
                f"Primary risk: {failed[0].title}. Please review findings before approval. "
                f"({reason}; running in deterministic mode)."
            )
        else:
            summary = (
                f"All deterministic checks passed. Evidence is internally consistent with vendor baseline. "
                f"({reason}; running in deterministic mode)."
            )

        return {
            "success": False,
            "model": "deterministic_fallback",
            "summary": summary,
            "confidence": "deterministic",
            "intent": {
                "requests_payment_detail_change": any("BENEFICIARY" in f.rule_id for f in failed),
                "claimed_new_beneficiary": ctx.get_field_val("email_claimed_account") or ctx.get_field_val("invoice_account_number"),
                "claims_prior_approval": False,
                "claimed_approver": None,
                "urgency_level": "normal",
                "supporting_quotes": [],
                "uncertainties": [reason],
            },
            "contradictions": [],
        }

payment_agent = PaymentVerificationAgent()
