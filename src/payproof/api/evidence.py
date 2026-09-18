from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from ..domain.models import EvidenceObject, User
from ..domain.errors import AuthorizationDeniedError, CaseNotFoundError
from ..repositories.case_repo import case_repo
from ..services.case_service import case_service
from ..config import settings
from .dependencies import get_current_user

router = APIRouter(prefix="/api/v1/cases/{case_id}/evidence", tags=["Evidence"])

@router.post("", response_model=EvidenceObject)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum upload size of {settings.max_upload_bytes / (1024*1024):.1f} MB"
        )

    try:
        evidence = case_service.ingest_evidence(
            actor=user,
            case_id=case_id,
            filename=file.filename or "unknown",
            content=content,
            mime_type=file.content_type or "application/octet-stream",
        )
        return evidence
    except AuthorizationDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except CaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("", response_model=list[EvidenceObject])
def list_evidence(case_id: str, user: User = Depends(get_current_user)):
    return case_repo.list_evidence_for_case(case_id)
