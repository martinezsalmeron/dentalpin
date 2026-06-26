"""Thin Kapso REST client (Meta WhatsApp Cloud API proxy).

Just the few calls the adapter + template sync need. Pattern mirrors
``verifactu/services/aeat_client.py``: an ``httpx.AsyncClient`` per call with a
timeout, mapping transport/4xx/5xx errors to a single ``KapsoError``.
"""

from __future__ import annotations

import httpx

KAPSO_BASE = "https://api.kapso.ai/meta/whatsapp/v24.0"
_TIMEOUT = 30.0


class KapsoError(Exception):
    """Any failure talking to Kapso (transport error or non-2xx response)."""


def template_payload(to: str, name: str, language: str, components: list[dict]) -> dict:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "template",
        "template": {"name": name, "language": {"code": language}, "components": components},
    }


def text_payload(to: str, body: str) -> dict:
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }


def build_named_components(context: dict) -> list[dict]:
    """Build a single body component from context using NAMED parameters.

    v1 constraint: the Meta template must use named variables matching the
    context keys (e.g. ``{{patient_name}}``). Internal keys are skipped.
    # ponytail: named params avoid needing a stored positional order; if a
    # clinic's template uses {{1}},{{2}} instead, map order at the mapping step.
    """
    skip = {"locale"}
    params = [
        {"type": "text", "parameter_name": k, "text": str(v)}
        for k, v in context.items()
        if k not in skip and v is not None
    ]
    return [{"type": "body", "parameters": params}] if params else []


async def _post(api_key: str, url: str, payload: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                url,
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json=payload,
            )
    except httpx.HTTPError as exc:
        raise KapsoError(f"HTTP error talking to Kapso: {exc}") from exc
    if resp.status_code >= 400:
        raise KapsoError(f"Kapso returned HTTP {resp.status_code}: {resp.text[:500]}")
    return resp.json()


async def _get(api_key: str, url: str, params: dict | None = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url, headers={"X-API-Key": api_key}, params=params)
    except httpx.HTTPError as exc:
        raise KapsoError(f"HTTP error talking to Kapso: {exc}") from exc
    if resp.status_code >= 400:
        raise KapsoError(f"Kapso returned HTTP {resp.status_code}: {resp.text[:500]}")
    return resp.json()


async def send_message(api_key: str, phone_number_id: str, payload: dict) -> dict:
    """POST a message. Returns the parsed response (``messages[0].id`` = wamid)."""
    return await _post(api_key, f"{KAPSO_BASE}/{phone_number_id}/messages", payload)


async def list_templates(api_key: str, business_account_id: str) -> list[dict]:
    """GET the WABA's message templates (all statuses)."""
    data = await _get(
        api_key,
        f"{KAPSO_BASE}/{business_account_id}/message_templates",
        params={"status": ["APPROVED", "PENDING", "REJECTED"]},
    )
    return data.get("data", [])
