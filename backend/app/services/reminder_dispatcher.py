import asyncio
import logging
from datetime import UTC, datetime

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config import get_settings
from app.database import SessionLocal
from app.models import Cat, Reminder
from app.services.i18n import t

log = logging.getLogger(__name__)


async def _fetch_due_batch(session: AsyncSession, limit: int = 25) -> list[Reminder]:
    now = datetime.now(tz=UTC)
    res = await session.execute(
        select(Reminder)
        .options(joinedload(Reminder.cat).joinedload(Cat.user))
        .where(
            Reminder.run_at <= now,
            Reminder.sent_at.is_(None),
            Reminder.cancelled.is_(False),
        )
        .order_by(Reminder.run_at.asc())
        .limit(limit)
    )
    return list(res.unique().scalars().all())


async def _try_mark_sent(session: AsyncSession, reminder_id: int) -> bool:
    now = datetime.now(tz=UTC)
    res = await session.execute(
        update(Reminder)
        .where(
            Reminder.id == reminder_id,
            Reminder.sent_at.is_(None),
            Reminder.cancelled.is_(False),
        )
        .values(sent_at=now, last_error=None)
        .returning(Reminder.id)
    )
    row = res.first()
    return row is not None


async def _mark_error(session: AsyncSession, reminder_id: int, err: str) -> None:
    await session.execute(
        update(Reminder)
        .where(Reminder.id == reminder_id)
        .values(last_error=err[:2000])
    )


async def reminder_loop(stop: asyncio.Event) -> None:
    settings = get_settings()
    bot = Bot(
        settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    while not stop.is_set():
        try:
            async with SessionLocal() as session:
                batch = await _fetch_due_batch(session)

            for rem in batch:
                user = rem.cat.user
                loc = user.locale or "en"
                payload = dict(rem.payload or {})
                text = t(loc, rem.message_key, **payload)
                try:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                    )
                except Exception as e:  # noqa: BLE001
                    log.exception("reminder_send_failed id=%s", rem.id)
                    async with SessionLocal() as err_session:
                        async with err_session.begin():
                            await _mark_error(err_session, rem.id, str(e))
                    continue

                async with SessionLocal() as ok_session:
                    async with ok_session.begin():
                        marked = await _try_mark_sent(ok_session, rem.id)
                    if not marked:
                        log.warning("reminder_already_sent id=%s", rem.id)
        except Exception:
            log.exception("reminder_batch_failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.reminder_poll_seconds)
        except TimeoutError:
            continue
    await bot.session.close()
