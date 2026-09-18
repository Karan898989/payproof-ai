import os
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from ..config import settings
from ..agents.nim_client import nim_client

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])

class UpdateKeyRequest(BaseModel):
    nvidia_api_key: str

@router.get("/status")
def get_status():
    has_key = nim_client.is_configured()
    masked_key = ""
    if has_key:
        k = settings.nvidia_api_key
        masked_key = f"{k[:4]}...{k[-4:]}" if len(k) > 8 else "***"

    return {
        "nim_configured": has_key,
        "masked_api_key": masked_key,
        "model": settings.nvidia_model,
        "base_url": settings.nvidia_base_url,
        "authz_mode": "Cedar Local Policy Engine",
        "app_env": settings.app_env,
    }

@router.post("/update-key")
def update_api_key(req: UpdateKeyRequest):
    new_key = req.nvidia_api_key.strip()
    settings.nvidia_api_key = new_key
    nim_client.api_key = new_key

    # Save to .env if possible
    env_path = Path(".env")
    lines = []
    found = False
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("NVIDIA_API_KEY="):
                    lines.append(f"NVIDIA_API_KEY={new_key}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"NVIDIA_API_KEY={new_key}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return {"success": True, "message": "NVIDIA API key updated successfully."}

@router.post("/test-nim")
async def test_nim_connection():
    result = await nim_client.test_connection()
    return result
