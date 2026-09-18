from fastapi import Request, Depends
from ..domain.models import User
from ..domain.enums import RoleName
from ..repositories.case_repo import case_repo

# Default system users for easy local demo switching
DEMO_USERS = {
    "analyst": User(id="u-analyst", username="analyst", full_name="Alex Chen (AP Analyst)", role=RoleName.ANALYST, email="analyst@payproof.local"),
    "approver": User(id="u-approver", username="approver", full_name="Morgan Vance (Finance Approver)", role=RoleName.APPROVER, email="approver@payproof.local"),
    "auditor": User(id="u-auditor", username="auditor", full_name="Sarah Miller (Internal Auditor)", role=RoleName.AUDITOR, email="auditor@payproof.local"),
    "admin": User(id="u-admin", username="admin", full_name="Dev Admin (System Admin)", role=RoleName.ADMIN, email="admin@payproof.local"),
}

def get_current_user(request: Request) -> User:
    # Check header or cookie for current role/user
    username = request.headers.get("X-PayProof-User") or request.cookies.get("payproof_user") or "analyst"
    username = username.lower().strip()
    return DEMO_USERS.get(username, DEMO_USERS["analyst"])
