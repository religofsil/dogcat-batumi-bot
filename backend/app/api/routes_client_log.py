import json
import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

from app.api.deps import CurrentUser

router = APIRouter(prefix="/api", tags=["client-log"])

log = logging.getLogger("app.client")

MAX_MESSAGE_LEN = 500
MAX_BODY_JSON_BYTES = 8192


class ClientLogIn(BaseModel):
    level: Literal["info", "warning", "error"]
    message: str = Field(max_length=MAX_MESSAGE_LEN)
    context: dict[str, Any] | None = None

    @field_validator("message")
    @classmethod
    def message_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty")
        return v


@router.post("/client-log")
async def client_log(request: Request, user: CurrentUser) -> dict[str, str]:
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
    body = ClientLogIn.model_validate(data)
    ctx = body.context
    ctx_str = ""
    if ctx is not None:
        try:
            ctx_str = json.dumps(ctx, ensure_ascii=False, default=str)[:4000]
        except TypeError:
            ctx_str = "<unserializable>"
    log.log(
        getattr(logging, body.level.upper()),
        "client user_id=%s message=%s context=%s",
        user.id,
        body.message[:MAX_MESSAGE_LEN],
        ctx_str,
    )
    return {"ok": "1"}
