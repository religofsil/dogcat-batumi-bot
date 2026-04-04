from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.database import get_db
from app.models import Cat, Reminder
from app.schemas.reminders import ReminderOut
from app.services.scenarios import ensure_cat_owned

router = APIRouter(prefix="/api/cats/{cat_id}/reminders", tags=["reminders"])
upcoming_router = APIRouter(prefix="/api/reminders", tags=["reminders"])


@router.get("", response_model=list[ReminderOut])
async def list_reminders(
    cat_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ReminderOut]:
    try:
        await ensure_cat_owned(db, user.id, cat_id)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found") from None
    res = await db.execute(
        select(Reminder).where(Reminder.cat_id == cat_id).order_by(Reminder.run_at.asc())
    )
    rows = res.scalars().all()
    return [ReminderOut.model_validate(r) for r in rows]


@upcoming_router.get("/upcoming", response_model=list[ReminderOut])
async def list_upcoming(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ReminderOut]:
    """All upcoming reminders across the curator's cats."""
    res = await db.execute(select(Cat.id).where(Cat.user_id == user.id))
    cat_ids = [r[0] for r in res.all()]
    if not cat_ids:
        return []
    res2 = await db.execute(
        select(Reminder)
        .where(
            Reminder.cat_id.in_(cat_ids),
            Reminder.sent_at.is_(None),
            Reminder.cancelled.is_(False),
        )
        .order_by(Reminder.run_at.asc())
    )
    rows = res2.scalars().all()
    return [ReminderOut.model_validate(r) for r in rows]
