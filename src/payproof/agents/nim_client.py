import os
import json
import logging
from typing import Any
import httpx
from ..config import settings

logger = logging.getLogger("payproof.nim")

class NimClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None):
        self._api_key = api_key
        self.base_url = (base_url or settings.nvidia_base_url).rstrip("/")
        self.model = model or settings.nvidia_model
        self.timeout = settings.nim_timeout_seconds

    @property
    def api_key(self) -> str:
        if self._api_key is not None:
            return self._api_key.strip()
        if settings.nvidia_api_key and settings.nvidia_api_key.strip():
            return settings.nvidia_api_key.strip()
        return os.getenv("NVIDIA_API_KEY", "").strip()

    @api_key.setter
    def api_key(self, val: str | None):
        self._api_key = val.strip() if val is not None else None

    def is_configured(self) -> bool:
        k = self.api_key
        return bool(
            k
            and len(k) > 5
            and not k.startswith("your_")
            and not k.startswith("nvapi-placeholder")
            and k != "..."
        )

    async def test_connection(self) -> dict[str, Any]:
        """Tests the NVIDIA NIM connection."""
        if not self.is_configured():
            return {"success": False, "message": "NVIDIA_API_KEY is not configured."}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": "Ping"}],
            "max_tokens": 5,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    return {"success": True, "message": f"Successfully connected to NVIDIA NIM ({self.model})"}
                else:
                    return {"success": False, "message": f"NVIDIA API responded with HTTP {res.status_code}: {res.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": f"Connection failed: {str(e)}"}

    async def generate_chat_completion(self, system_prompt: str, user_prompt: str) -> str | None:
        if not self.is_configured():
            logger.info("NVIDIA API key not configured; skipping NIM inference.")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1500,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                if res.status_code != 200:
                    logger.warning("NIM API returned status %d: %s", res.status_code, res.text[:200])
                    return None
                data = res.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                return None
        except httpx.TimeoutException:
            logger.warning("NIM API call timed out after %s seconds", self.timeout)
            return None
        except Exception as e:
            logger.warning("NIM API call failed: %s", str(e))
            return None

nim_client = NimClient()
