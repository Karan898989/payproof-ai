from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from .config import settings
from .repositories.db import init_db
from .repositories.case_repo import case_repo
from .api.dependencies import get_current_user, DEMO_USERS
from .api.cases import router as cases_router
from .api.evidence import router as evidence_router
from .api.review import router as review_router
from .api.settings import router as settings_router
from .agents.nim_client import nim_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database initialized
    init_db()
    
    # Initialize demo users if not present
    for u in DEMO_USERS.values():
        case_repo.create_user(u)
        
    yield

app = FastAPI(
    title="PayProof AI",
    description="Evidence-bound pre-payment verification layer powered by NVIDIA Nemotron and Cedar IAM",
    version="0.1.0",
    lifespan=lifespan,
)

# Static and Templates
web_dir = Path(__file__).parent / "web"
static_dir = web_dir / "static"
templates_dir = web_dir / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Include API Routers
app.include_router(cases_router)
app.include_router(evidence_router)
app.include_router(review_router)
app.include_router(settings_router)

# Health Endpoints
@app.get("/health/live")
def health_live():
    return {"status": "ok", "service": "payproof-ai"}

@app.get("/health/ready")
def health_ready():
    return {
        "status": "ready",
        "database": settings.database_path.exists(),
        "nim_configured": nim_client.is_configured(),
        "model": settings.nvidia_model,
    }

# Web UI Routes
@app.get("/", response_class=HTMLResponse)
def index_view(request: Request, current_user=Depends(get_current_user)):
    cases = case_repo.list_cases()
    return templates.TemplateResponse(
        request=request,
        name="cases_list.html",
        context={
            "cases": cases,
            "current_user": current_user,
            "nim_configured": nim_client.is_configured(),
        }
    )

@app.get("/cases/{case_id}", response_class=HTMLResponse)
def case_detail_view(case_id: str, request: Request, current_user=Depends(get_current_user)):
    case = case_repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    evidence = case_repo.list_evidence_for_case(case_id)
    findings = case_repo.get_findings_for_case(case_id)
    decision = case_repo.get_decision_for_case(case_id)
    vendor = case_repo.get_vendor(case.vendor_id) if case.vendor_id else None
    
    # Try finding matching purchase order
    po = case_repo.get_po_by_vendor(case.vendor_id) if case.vendor_id else None

    callback = case_repo.get_verification_callback(case_id)
    audit_events = case_repo.list_audit_events_for_case(case_id)

    return templates.TemplateResponse(
        request=request,
        name="case_detail.html",
        context={
            "case": case,
            "evidence": evidence,
            "findings": findings,
            "decision": decision,
            "vendor": vendor,
            "purchase_order": po,
            "verification_callback": callback,
            "audit_events": audit_events,
            "current_user": current_user,
            "nim_configured": nim_client.is_configured(),
        }
    )
