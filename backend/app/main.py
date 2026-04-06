import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram.types import Update
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_auth import router as auth_router
from app.api.routes_cats import router as cats_router
from app.api.routes_client_bootstrap_log import router as client_bootstrap_log_router
from app.api.routes_client_log import router as client_log_router
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
from app.logging_setup import configure_logging
from app.middleware.request_logging import RequestLoggingMiddleware
from app.services.reminder_dispatcher import reminder_loop

log = logging.getLogger(__name__)


def _telegram_update_event_type(update: Update) -> str:
    for name in (
        "message",
        "edited_message",
        "channel_post",
        "edited_channel_post",
        "inline_query",
        "chosen_inline_result",
        "callback_query",
        "shipping_query",
        "pre_checkout_query",
        "poll",
        "poll_answer",
        "my_chat_member",
        "chat_member",
        "chat_join_request",
        "message_reaction",
        "message_reaction_count",
        "chat_boost",
        "removed_chat_boost",
        "business_connection",
        "business_message",
        "edited_business_message",
        "deleted_business_messages",
    ):
        if getattr(update, name, None) is not None:
            return name
    return "unknown"


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
        log.info("webhook_set url=%s", settings.webhook_url)

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
    configure_logging(settings.log_level)
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
    # Outermost: runs first on request — logs final status and sets X-Request-ID.
    app.add_middleware(RequestLoggingMiddleware)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, HTTPException):
            return await http_exception_handler(request, exc)
        rid = getattr(request.state, "request_id", None)
        log.exception("unhandled request_id=%s path=%s", rid, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "internal_server_error"},
        )

    app.include_router(auth_router)
    app.include_router(cats_router)
    app.include_router(client_bootstrap_log_router)
    app.include_router(client_log_router)
    app.include_router(debug_router)
    app.include_router(dosage_router)
    app.include_router(reminders_router)
    app.include_router(reminders_upcoming_router)
    app.include_router(scenarios_router)
    app.include_router(templates_router)
    app.include_router(user_router)

    app.mount(
        "/uploads",
        StaticFiles(directory=str(settings.upload_root)),
        name="uploads",
    )

    static_dir = Path(__file__).resolve().parent / "static" / "miniapp"
    if static_dir.is_dir():
        mini_root = settings.miniapp_path.rstrip("/") or "/miniapp"
        index_html = static_dir / "index.html"
        # StaticFiles mounted at /miniapp issues 307 /miniapp -> /miniapp/. Telegram Desktop's
        # WebView often does not follow that redirect, so the bundle never runs (no /api/*).
        @app.get(mini_root, include_in_schema=False)
        async def miniapp_entry_no_trailing_slash() -> FileResponse:
            return FileResponse(index_html)

        app.mount(
            f"{mini_root}/",
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
        log.info(
            "telegram_webhook update_id=%s event_type=%s",
            update.update_id,
            _telegram_update_event_type(update),
        )
        await dp.feed_update(bot, update)
        return {"ok": True}

    return app


app = create_app()
