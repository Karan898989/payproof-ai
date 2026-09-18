from pydantic import BaseModel, Field

class PaymentChangeIntent(BaseModel):
    requests_payment_detail_change: bool = Field(
        description="Whether the communication is requesting changes to payment details, routing, or bank account."
    )
    claimed_new_beneficiary: str | None = Field(
        default=None,
        description="Claimed new beneficiary account, routing, or bank details mentioned in the text."
    )
    claims_prior_approval: bool = Field(
        default=False,
        description="Whether the sender claims that an executive or manager has already approved the change."
    )
    claimed_approver: str | None = Field(
        default=None,
        description="Name or title of any claimed approver."
    )
    urgency_level: str = Field(
        default="normal",
        description="Expressed urgency: low, normal, high, or critical/immediate."
    )
    supporting_quotes: list[str] = Field(
        default_factory=list,
        description="Exact quoted text snippets from the evidence supporting the determination."
    )
    uncertainties: list[str] = Field(
        default_factory=list,
        description="Any ambiguous or uncertain points in the text."
    )

class ContradictionItem(BaseModel):
    statement_a: str
    statement_b: str
    explanation: str

class SemanticAnalysisResult(BaseModel):
    intent: PaymentChangeIntent
    contradictions: list[ContradictionItem] = Field(default_factory=list)
    executive_summary: str = Field(
        description="Concise 2-3 sentence executive summary for the accounts payable reviewer."
    )
    confidence: str = "high"
