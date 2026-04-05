from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.database import get_db
from app.schemas.user import DailyReminderTimeUpdate, LocaleUpdate, UserOut

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("", response_model=UserOut)
async def read_me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/locale", response_model=UserOut)
async def update_locale(
    body: LocaleUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    user.locale = body.locale
    await db.flush()
    return UserOut.model_validate(user)


@router.patch("/daily-reminder-time", response_model=UserOut)
async def update_daily_reminder_time(
    body: DailyReminderTimeUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    user.daily_reminder_time = body.daily_reminder_time
    await db.flush()
    return UserOut.model_validate(user)
