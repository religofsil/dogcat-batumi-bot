import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import parse_qsl

from app.config import get_settings


def validate_init_data(init_data: str, max_age_seconds: int = 86400) -> dict[str, Any]:
    """
    Validate Telegram Mini App initData per
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    settings = get_settings()
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("missing_hash")

    auth_date_raw = parsed.get("auth_date")
    if auth_date_raw is None:
        raise ValueError("missing_auth_date")
    auth_date = int(auth_date_raw)
    if time.time() - auth_date > max_age_seconds:
        raise ValueError("init_data_expired")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(
        b"WebAppData", settings.bot_token.encode("utf-8"), hashlib.sha256
    ).digest()
    calculated = hmac.new(
        secret_key, data_check_string.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise ValueError("bad_hash")

    user_raw = parsed.get("user")
    if not user_raw:
        raise ValueError("missing_user")
    user = json.loads(user_raw)
    telegram_id = user.get("id")
    if telegram_id is None:
        raise ValueError("missing_telegram_id")
    language_code = user.get("language_code") or "en"
    return {"telegram_id": int(telegram_id), "language_code": str(language_code), "user": user}
