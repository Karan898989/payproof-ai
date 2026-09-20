import os
from pathlib import Path
from pydantic import BaseModel

class Settings(BaseModel):
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    
    # Storage
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    database_path: Path = Path(".var/payproof.db")
    evidence_store_path: Path = Path(".var/evidence")
    decision_policy_path: Path = Path("config/decision_policy.yaml")
    
    # NVIDIA NIM & Nemotron
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "nvidia/nemotron-3-ultra-550b-a55b"
    nim_timeout_seconds: float = 30.0
    nim_enabled: bool = True
    
    # Security
    max_upload_bytes: int = 15 * 1024 * 1024  # 15 MB

    @classmethod
    def load(cls) -> "Settings":
        base_dir = Path(__file__).resolve().parent.parent.parent
        # Load from .env if present
        for ep in (Path(".env"), base_dir / ".env"):
            if ep.exists():
                with open(ep, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        db_p = Path(os.getenv("DATABASE_PATH", ".var/payproof.db"))
        if not db_p.is_absolute():
            db_p = base_dir / db_p

        ev_p = Path(os.getenv("EVIDENCE_STORE_PATH", ".var/evidence"))
        if not ev_p.is_absolute():
            ev_p = base_dir / ev_p

        pol_p = Path(os.getenv("DECISION_POLICY_PATH", "config/decision_policy.yaml"))
        if not pol_p.is_absolute():
            pol_p = base_dir / pol_p

        return cls(
            app_env=os.getenv("APP_ENV", "development"),
            app_host=os.getenv("APP_HOST", "127.0.0.1"),
            app_port=int(os.getenv("APP_PORT", "8000")),
            base_dir=base_dir,
            database_path=db_p,
            evidence_store_path=ev_p,
            decision_policy_path=pol_p,
            nvidia_api_key=os.getenv("NVIDIA_API_KEY", "").strip(),
            nvidia_base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            nvidia_model=os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"),
            nim_timeout_seconds=float(os.getenv("NIM_TIMEOUT_SECONDS", "30.0")),
            nim_enabled=os.getenv("NIM_ENABLED", "true").lower() in ("1", "true", "yes"),
        )

settings = Settings.load()
