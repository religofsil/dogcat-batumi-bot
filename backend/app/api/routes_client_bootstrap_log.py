"""Pre-session client events (Telegram WebView init, JS errors) — no auth."""

import json
import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, field_validator

router = APIRouter(prefix="/api", tags=["client-log"])

log = logging.getLogger("app.client.bootstrap")

MAX_BODY_JSON_BYTES = 2048
MAX_CONTEXT_KEYS = 32


class BootstrapLogIn(BaseModel):
    event: Literal[
        "no_init_data",
        "auth_failed",
        "window_error",
        "unhandled_rejection",
        "boot_failed",
    ]
    context: dict[str, str | int | float | bool | None] | None = None

    @field_validator("context")
    @classmethod
    def limit_context(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is None:
            return None
        if len(v) > MAX_CONTEXT_KEYS:
            raise ValueError("context too large")
        return v


@router.post("/client-log/bootstrap")
async def client_bootstrap_log(request: Request) -> dict[str, str]:
    raw_bytes = await request.body()
    if len(raw_bytes) > MAX_BODY_JSON_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="payload_too_large",
        )
    try:
        data = json.loads(raw_bytes)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_json",
        ) from e
    body = BootstrapLogIn.model_validate(data)
    rid = getattr(request.state, "request_id", None)
    ctx_str = ""
    if body.context:
        try:
            ctx_str = json.dumps(body.context, ensure_ascii=False, default=str)[:1500]
        except TypeError:
            ctx_str = "<unserializable>"
    log.warning(
        "bootstrap event=%s request_id=%s context=%s",
        body.event,
        rid,
        ctx_str,
    )
    return {"ok": "1"}
