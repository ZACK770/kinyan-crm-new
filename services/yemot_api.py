import logging
from typing import Any, Dict

import httpx

from db import settings

logger = logging.getLogger(__name__)


class YemotAPIError(Exception):
    def __init__(self, response_status: str, message: str | None = None, raw: Dict[str, Any] | None = None):
        self.response_status = response_status
        self.message = message or ""
        self.raw = raw or {}
        super().__init__(f"Yemot API error: {response_status} {self.message}".strip())


async def run_tzintuk(
    phone: str,
    *,
    caller_id: str = "RAND",
    timeout_seconds: float | None = None,
) -> Dict[str, Any]:
    """Call Yemot/Call2All RunTzintuk.

    Returns the parsed JSON response.
    Raises YemotAPIError on non-OK responseStatus.
    """
    if not settings.YEMOT_TOKEN:
        raise ValueError("YEMOT_TOKEN is not configured")

    base = settings.YEMOT_API_BASE_URL.rstrip("/") + "/"
    url = f"{base}RunTzintuk"

    tz_timeout = timeout_seconds if timeout_seconds is not None else settings.YEMOT_TZINTUK_TIMEOUT_SECONDS

    params = {
        "token": settings.YEMOT_TOKEN,
        "callerId": caller_id,
        "TzintukTimeOut": tz_timeout,
        "phones": phone,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    status = (data or {}).get("responseStatus")
    if status != "OK":
        raise YemotAPIError(status or "UNKNOWN", (data or {}).get("message"), data)

    return data
