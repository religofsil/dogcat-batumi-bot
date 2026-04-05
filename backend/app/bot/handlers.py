from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    KeyboardButton,
    MenuButtonWebApp,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models import User
from app.services.i18n import bot_message, normalize_locale
from app.services.scenarios import get_or_create_user

router = Router(name="main")


def _miniapp_url() -> str:
    """Telegram Web Apps work best with a trailing slash on the app root."""
    settings = get_settings()
    base = settings.miniapp_url.rstrip("/")
    return f"{base}/"


async def ensure_menu_button(bot, *, chat_id: int | None = None) -> None:
    url = _miniapp_url()
    menu = MenuButtonWebApp(text="Open app", web_app=WebAppInfo(url=url))
    if chat_id is not None:
        await bot.set_chat_menu_button(chat_id=chat_id, menu_button=menu)
    else:
        await bot.set_chat_menu_button(menu_button=menu)


@router.message(CommandStart(), F.chat.type == ChatType.PRIVATE)
async def cmd_start(message: Message) -> None:
    if not message.from_user:
        return
    async with SessionLocal() as session:
        async with session.begin():
            user = await get_or_create_user(
                session,
                message.from_user.id,
                message.from_user.language_code,
            )
            loc = user.locale
        text = bot_message(loc, "start", miniapp_url=_miniapp_url())
    url = _miniapp_url()
    # Visible Web App button (works even if the ⋮ menu button is easy to miss).
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Open app", web_app=WebAppInfo(url=url))]],
        resize_keyboard=True,
    )
    await message.answer(text, reply_markup=kb)
    await ensure_menu_button(message.bot, chat_id=message.chat.id)


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
