"""Open Policy Agent (OPA) client utility for gateway & pipeline checks."""

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def check_opa_policy(
    organization_id: str,
    role: str,
    scopes: list[str],
    action: str,
    resource: str,
) -> tuple[bool, str | None]:
    """Query the local/sidecar OPA service to authorize gateway HTTP requests.

    Returns (allow, reason).
    """
    settings = get_settings()
    url = f"{settings.opa_url}/v1/data/autofounder/auth/allow"
    payload = {
        "input": {
            "organization_id": organization_id,
            "role": role,
            "scopes": scopes,
            "action": action,
            "resource": resource,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                result_wrapper = response.json()
                result = result_wrapper.get("result")
                if result is None:
                    return False, "Policy not defined in OPA"

                if isinstance(result, bool):
                    return result, None

                if isinstance(result, dict):
                    allow = result.get("allow", False)
                    reason = result.get("reason")
                    return allow, reason

                return False, "Invalid OPA response format"
            else:
                msg = f"OPA service returned status code {response.status_code}"
                logger.error(msg)
                if not settings.is_production:
                    return True, f"Dev bypass (non-200 from OPA): {msg}"
                return False, msg
    except httpx.RequestError as e:
        msg = f"Failed to connect to OPA service: {e}"
        logger.warning(msg)
        if not settings.is_production:
            return True, f"Dev bypass (OPA offline): {msg}"
        return False, msg
