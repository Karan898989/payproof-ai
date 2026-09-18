from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from ..domain.models import User, PaymentCase, AuditEvent, VerificationCallbackRecord
from ..domain.errors import AuthorizationDeniedError, CaseNotFoundError, InvalidStateTransitionError
from ..repositories.case_repo import case_repo
from ..services.case_service import case_service
from .dependencies import get_current_user

router = APIRouter(prefix="/api/v1/cases/{case_id}", tags=["Review & Actions"])

class RecordVerificationRequest(BaseModel):
    callback_phone_used: str
    vendor_contact_spoken: str
    confirmation_method: str = "Voice Phone Callback"
    is_confirmed: bool = True
    notes: str = ""

class OverrideHoldRequest(BaseModel):
    override_reason: str

class DispositionRequest(BaseModel):
    notes: str = ""

@router.post("/record-verification", response_model=VerificationCallbackRecord)
def record_verification(
    case_id: str,
    req: RecordVerificationRequest,
    user: User = Depends(get_current_user)
):
    try:
        rec = case_service.record_verification(
            actor=user,
            case_id=case_id,
            callback_phone_used=req.callback_phone_used,
            vendor_contact_spoken=req.vendor_contact_spoken,
            confirmation_method=req.confirmation_method,
            is_confirmed=req.is_confirmed,
            notes=req.notes,
        )
        return rec
    except AuthorizationDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/override", response_model=PaymentCase)
def override_hold(
    case_id: str,
    req: OverrideHoldRequest,
    user: User = Depends(get_current_user)
):
    try:
        case = case_service.override_hold(
            actor=user,
            case_id=case_id,
            override_reason=req.override_reason,
        )
        return case
    except AuthorizationDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/disposition", response_model=PaymentCase)
def approve_disposition(
    case_id: str,
    req: DispositionRequest,
    user: User = Depends(get_current_user)
):
    try:
        case = case_service.approve_disposition(
            actor=user,
            case_id=case_id,
            notes=req.notes,
        )
        return case
    except AuthorizationDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/audit", response_model=list[AuditEvent])
def get_case_audit(case_id: str, user: User = Depends(get_current_user)):
    return case_repo.list_audit_events_for_case(case_id)
