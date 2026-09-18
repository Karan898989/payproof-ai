from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from ..domain.models import PaymentCase, Finding, Decision, User
from ..domain.errors import AuthorizationDeniedError, CaseNotFoundError
from ..repositories.case_repo import case_repo
from ..services.case_service import case_service
from ..services.export_service import export_service
from .dependencies import get_current_user

router = APIRouter(prefix="/api/v1/cases", tags=["Cases"])

class CreateCaseRequest(BaseModel):
    case_number: str
    vendor_id: str | None = None
    vendor_name: str | None = None
    amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    invoice_reference: str | None = None

@router.post("", response_model=PaymentCase)
def create_case(req: CreateCaseRequest, user: User = Depends(get_current_user)):
    try:
        case = case_service.create_case(
            actor=user,
            case_number=req.case_number,
            vendor_id=req.vendor_id,
            vendor_name=req.vendor_name,
            amount=req.amount,
            currency=req.currency,
            invoice_reference=req.invoice_reference,
        )
        return case
    except AuthorizationDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("", response_model=list[PaymentCase])
def list_cases(user: User = Depends(get_current_user)):
    return case_repo.list_cases()

@router.get("/{case_id}", response_model=PaymentCase)
def get_case(case_id: str, user: User = Depends(get_current_user)):
    case = case_repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case

@router.post("/{case_id}/analyze")
async def analyze_case(case_id: str, user: User = Depends(get_current_user)):
    try:
        decision = await case_service.analyze_case(actor=user, case_id=case_id)
        findings = case_repo.get_findings_for_case(case_id)
        return {"decision": decision, "findings": findings}
    except AuthorizationDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{case_id}/findings", response_model=list[Finding])
def get_findings(case_id: str, user: User = Depends(get_current_user)):
    return case_repo.get_findings_for_case(case_id)

@router.get("/{case_id}/decision", response_model=Decision | None)
def get_decision(case_id: str, user: User = Depends(get_current_user)):
    return case_repo.get_decision_for_case(case_id)

@router.get("/{case_id}/export")
def export_case(case_id: str, user: User = Depends(get_current_user)):
    dossier = export_service.export_case_dossier(case_id)
    if not dossier:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return dossier
