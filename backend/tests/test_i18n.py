from app.services.i18n import normalize_locale, t


def test_normalize_locale() -> None:
    assert normalize_locale("ru-RU") == "ru"
    assert normalize_locale("xx") == "en"


def test_t_fallback() -> None:
    text = t("en", "bot.help")
    assert len(text) > 5
