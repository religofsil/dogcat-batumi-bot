from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Cat, Reminder, ScenarioRun, ScenarioStatus, ScenarioType, User


def _localize_anchor(anchor: datetime, tz_name: str) -> datetime:
    if anchor.tzinfo is None:
        anchor = anchor.replace(tzinfo=UTC)
    return anchor.astimezone(ZoneInfo(tz_name))


def _at_local_day_start(
    anchor_local: datetime,
    day_offset: int,
    hour: int,
    minute: int,
) -> datetime:
    day = anchor_local.date() + timedelta(days=day_offset)
    local = datetime(
        day.year, day.month, day.day, hour, minute, tzinfo=anchor_local.tzinfo
    )
    return local.astimezone(UTC)


async def ensure_cat_owned(db: AsyncSession, user_id: int, cat_id: int) -> Cat:
    res = await db.execute(
        select(Cat).where(Cat.id == cat_id, Cat.user_id == user_id)
    )
    cat = res.scalar_one_or_none()
    if cat is None:
        raise PermissionError("cat_not_found")
    return cat


async def cancel_active_runs(
    db: AsyncSession, cat_id: int, scenario_type: ScenarioType
) -> None:
    res = await db.execute(
        select(ScenarioRun).where(
            ScenarioRun.cat_id == cat_id,
            ScenarioRun.scenario_type == scenario_type,
            ScenarioRun.status == ScenarioStatus.active,
        )
    )
    for run in res.scalars():
        run.status = ScenarioStatus.cancelled
        await db.execute(
            update(Reminder)
            .where(
                Reminder.scenario_run_id == run.id,
                Reminder.sent_at.is_(None),
            )
            .values(cancelled=True)
        )
    await db.flush()


async def schedule_reminders_for_run(
    db: AsyncSession,
    run: ScenarioRun,
    *,
    default_tz: str,
    anchor: datetime | None = None,
) -> list[Reminder]:
    cat_res = await db.execute(select(Cat).where(Cat.id == run.cat_id))
    cat = cat_res.scalar_one()
    anchor = anchor or datetime.now(tz=UTC)
    anchor_local = _localize_anchor(anchor, default_tz)
    reminders: list[Reminder] = []

    def add(kind: str, message_key: str, run_at: datetime, payload: dict[str, Any] | None = None):
        reminders.append(
            Reminder(
                cat_id=cat.id,
                scenario_run_id=run.id,
                kind=kind,
                message_key=message_key,
                run_at=run_at,
                cancelled=False,
                payload={**(payload or {}), "cat_name": cat.name},
            )
        )

    st = run.scenario_type
    if st == ScenarioType.adopted_home:
        # Day 1..14 local mornings
        for day in range(1, 15):
            key = f"reminders.adopted_home.day_{day}"
            rt = _at_local_day_start(anchor_local, day, 9, 0)
            add(f"adopted_day_{day}", key, rt, {"day": day})
    elif st == ScenarioType.new_capture:
        add("capture_intro", "reminders.new_capture.intro", anchor_local.astimezone(UTC))
        add(
            "capture_day1",
            "reminders.new_capture.day_1",
            _at_local_day_start(anchor_local, 1, 10, 0),
        )
        add(
            "capture_day3",
            "reminders.new_capture.day_3",
            _at_local_day_start(anchor_local, 3, 10, 0),
        )
        add(
            "capture_day7",
            "reminders.new_capture.day_7",
            _at_local_day_start(anchor_local, 7, 10, 0),
        )
    elif st == ScenarioType.post_prep:
        days = int((run.context or {}).get("post_delay_days", 2))
        rt = _at_local_day_start(anchor_local, days, 11, 0)
        add("post_prep", "reminders.post_prep.reminder", rt)
    elif st == ScenarioType.sterilization:
        op_raw = (run.context or {}).get("operation_at")
        if not op_raw:
            raise ValueError("operation_at_required")
        op_at = datetime.fromisoformat(str(op_raw))
        if op_at.tzinfo is None:
            op_at = op_at.replace(tzinfo=ZoneInfo(default_tz))
        op_at = op_at.astimezone(UTC)
        add(
            "sterile_food",
            "reminders.sterilization.remove_food",
            op_at - timedelta(hours=12),
            {"op_at": op_at.isoformat()},
        )
        add(
            "sterile_water",
            "reminders.sterilization.remove_water",
            op_at - timedelta(hours=8),
            {"op_at": op_at.isoformat()},
        )
        add(
            "sterile_op",
            "reminders.sterilization.operation",
            op_at,
            {"op_at": op_at.isoformat()},
        )
    elif st == ScenarioType.potential_adopter:
        # Templates-only scenario: optional nudge after 3 days
        rt = _at_local_day_start(anchor_local, 3, 12, 0)
        add("adopter_nudge", "reminders.potential_adopter.nudge", rt)

    for r in reminders:
        db.add(r)
    await db.flush()
    return reminders


async def start_scenario(
    db: AsyncSession,
    *,
    user_id: int,
    cat_id: int,
    scenario_type: ScenarioType,
    default_tz: str,
    anchor: datetime | None = None,
    context: dict[str, Any] | None = None,
) -> ScenarioRun:
    await ensure_cat_owned(db, user_id, cat_id)
    await cancel_active_runs(db, cat_id, scenario_type)
    run = ScenarioRun(
        cat_id=cat_id,
        scenario_type=scenario_type,
        status=ScenarioStatus.active,
        context=context,
    )
    db.add(run)
    await db.flush()
    await schedule_reminders_for_run(db, run, default_tz=default_tz, anchor=anchor)
    await db.refresh(run)
    return run


async def load_user_for_telegram(db: AsyncSession, telegram_id: int) -> User | None:
    res = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return res.scalar_one_or_none()


async def get_or_create_user(
    db: AsyncSession, telegram_id: int, locale_hint: str | None
) -> User:
    from app.services.i18n import normalize_locale

    user = await load_user_for_telegram(db, telegram_id)
    if user:
        return user
    loc = normalize_locale(locale_hint)
    user = User(telegram_id=telegram_id, locale=loc)
    db.add(user)
    await db.flush()
    return user


async def get_cat_with_user(db: AsyncSession, cat_id: int) -> tuple[Cat, User] | None:
    res = await db.execute(
        select(Cat).options(selectinload(Cat.user)).where(Cat.id == cat_id)
    )
    cat = res.scalar_one_or_none()
    if cat is None:
        return None
    return cat, cat.user
