from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings


def create_session_token(user_id: int, telegram_id: int) -> str:
    settings = get_settings()
    now = datetime.now(tz=UTC)
    payload = {
        "uid": user_id,
        "tid": telegram_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.session_expire_days)).timestamp()),
    }
    return jwt.encode(payload, settings.session_secret, algorithm="HS256")


def decode_session_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.session_secret, algorithms=["HS256"])
