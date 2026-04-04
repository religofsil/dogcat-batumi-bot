from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, MenuButtonWebApp, Message, WebAppInfo
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models import User
from app.services.i18n import bot_message, normalize_locale
from app.services.scenarios import get_or_create_user

router = Router(name="main")


async def ensure_menu_button(bot) -> None:
    settings = get_settings()
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="Open app", web_app=WebAppInfo(url=settings.miniapp_url))
    )


@router.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def cmd_start(message: Message) -> None:
    if not message.from_user:
        return
    settings = get_settings()
    async with SessionLocal() as session:
        async with session.begin():
            user = await get_or_create_user(
                session,
                message.from_user.id,
                message.from_user.language_code,
            )
            loc = user.locale
        text = bot_message(loc, "start", miniapp_url=settings.miniapp_url)
    await message.answer(text)
    await ensure_menu_button(message.bot)


@router.message(Command("help"), F.chat.type == ChatType.PRIVATE)
async def cmd_help(message: Message) -> None:
    if not message.from_user:
        return
    async with SessionLocal() as session:
        res = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = res.scalar_one_or_none()
        loc = user.locale if user else normalize_locale(message.from_user.language_code)
    await message.answer(bot_message(loc, "help"))


async def register_bot_commands(bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Start"),
            BotCommand(command="help", description="Help"),
        ]
    )
