import json
from functools import lru_cache
from pathlib import Path

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"
FALLBACK = "en"
SUPPORTED = {"en", "ru", "ka"}


def normalize_locale(code: str | None) -> str:
    if not code:
        return FALLBACK
    base = code.split("-")[0].lower()
    return base if base in SUPPORTED else FALLBACK


@lru_cache
def _load_locale_file(locale: str) -> dict:
    path = LOCALES_DIR / f"{locale}.json"
    if not path.exists():
        path = LOCALES_DIR / f"{FALLBACK}.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _get_path(data: dict, dotted: str) -> str:
    cur: object = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(dotted)
        cur = cur[part]
    if not isinstance(cur, str):
        raise KeyError(dotted)
    return cur


def t(locale: str, key: str, **kwargs: object) -> str:
    loc = normalize_locale(locale)
    try:
        template = _get_path(_load_locale_file(loc), key)
    except KeyError:
        template = _get_path(_load_locale_file(FALLBACK), key)
    try:
        return template.format(**kwargs)
    except Exception:
        return template


def bot_message(locale: str, key: str, **kwargs: object) -> str:
    return t(locale, f"bot.{key}", **kwargs)
