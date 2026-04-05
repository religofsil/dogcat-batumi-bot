import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_auth import router as auth_router
from app.api.routes_cats import router as cats_router
from app.api.routes_debug import router as debug_router
from app.api.routes_dosage import router as dosage_router
from app.api.routes_reminders import router as reminders_router
from app.api.routes_reminders import upcoming_router as reminders_upcoming_router
from app.api.routes_scenarios import router as scenarios_router
from app.api.routes_templates import router as templates_router
from app.api.routes_user import router as user_router
from app.bot.handlers import register_bot_commands
from app.bot.setup import build_bot, build_dispatcher
from app.config import get_settings
from app.services.reminder_dispatcher import reminder_loop

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    bot = build_bot()
    dp = build_dispatcher()
    app.state.bot = bot
    app.state.dp = dp

    stop = asyncio.Event()
    reminder_task = asyncio.create_task(reminder_loop(stop))

    await register_bot_commands(bot)
    if settings.set_webhook_on_startup:
        await bot.set_webhook(
            url=settings.webhook_url,
            secret_token=settings.telegram_webhook_secret or None,
        )
        log.info("webhook_set", extra={"url": settings.webhook_url})

    try:
        yield
    finally:
        stop.set()
        reminder_task.cancel()
        try:
            await reminder_task
        except asyncio.CancelledError:
            pass
        await bot.session.close()


def create_app() -> FastAPI:
    settings = get_settings()
    settings.upload_root.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title="Batumi curator bot", lifespan=lifespan)

    origins = list({*settings.cors_origin_list, settings.public_base_url.rstrip("/")})
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(debug_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(cats_router)
    app.include_router(scenarios_router)
    app.include_router(reminders_router)
    app.include_router(reminders_upcoming_router)
    app.include_router(dosage_router)
    app.include_router(templates_router)

    app.mount(
        "/uploads",
        StaticFiles(directory=str(settings.upload_root)),
        name="uploads",
    )

    static_dir = Path(__file__).resolve().parent / "static" / "miniapp"
    if static_dir.is_dir():
        app.mount(
            settings.miniapp_path,
            StaticFiles(directory=static_dir, html=True),
            name="miniapp",
        )

    @app.get("/")
    async def root():
        return {"status": "ok", "service": "batumi-curator-bot"}

    @app.get("/healthz")
    async def healthz():
        return {"ok": True}

    @app.post("/webhook/{secret}")
    async def telegram_webhook(secret: str, request: Request):
        if secret != settings.webhook_path_secret:
            raise HTTPException(status_code=404, detail="not_found")
        if settings.telegram_webhook_secret:
            hdr = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if hdr != settings.telegram_webhook_secret:
                raise HTTPException(status_code=401, detail="unauthorized")
        bot = request.app.state.bot
        dp = request.app.state.dp
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot, update)
        return {"ok": True}

    return app


app = create_app()
