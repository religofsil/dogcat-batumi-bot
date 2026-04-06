import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas.user import UserOut
from app.services.i18n import normalize_locale
from app.services.scenarios import get_or_create_user
from app.services.sessions import create_session_token
from app.services.telegram_webapp import validate_init_data

router = APIRouter(prefix="/api/auth", tags=["auth"])

log = logging.getLogger(__name__)


class TelegramAuthBody(BaseModel):
    init_data: str = Field(min_length=10)


@router.post("/telegram", response_model=UserOut)
async def auth_telegram(
    body: TelegramAuthBody,
    response: Response,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    settings = get_settings()
    try:
        parsed = validate_init_data(body.init_data)
    except ValueError as e:
        rid = getattr(request.state, "request_id", None)
        log.warning("auth_validation_failed request_id=%s", rid)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)) from e

    user = await get_or_create_user(db, parsed["telegram_id"], parsed.get("language_code"))
    hint = normalize_locale(parsed.get("language_code"))
    if user.locale != hint and hint != "en":
        user.locale = hint
    await db.flush()

    token = create_session_token(user.id, user.telegram_id)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="none" if settings.secure_cookies else "lax",
        max_age=int(timedelta(days=settings.session_expire_days).total_seconds()),
        path="/",
    )
    return UserOut.model_validate(user)


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name, path="/")
    return {"message": "ok"}
