import logging
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    webhook_path_secret: str
    telegram_webhook_secret: str = ""
    public_base_url: str
    miniapp_path: str = "/miniapp"

    database_url: str

    session_secret: str
    session_cookie_name: str = "curator_session"
    session_expire_days: int = 7

    default_tz: str = "Asia/Tbilisi"

    cors_origins: str = "https://web.telegram.org"

    reminder_poll_seconds: int = 45
    set_webhook_on_startup: bool = False
    secure_cookies: bool = True

    log_level: str = "INFO"


    upload_root: Path = Path("/app/data/uploads")
    max_upload_bytes: int = 10_485_760  # 10 MiB

    # Optional: absolute path on the API host for miniapp NDJSON debug logs (Cursor debug sessions).
    client_debug_log_path: str | None = None

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        name = (v or "INFO").upper()
        if name not in logging.getLevelNamesMapping():
            return "INFO"
        return name

    @property
    def miniapp_url(self) -> str:
        return f"{self.public_base_url.rstrip('/')}{self.miniapp_path}"

    @property
    def webhook_url(self) -> str:
        return f"{self.public_base_url.rstrip('/')}/webhook/{self.webhook_path_secret}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
