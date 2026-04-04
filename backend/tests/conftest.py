import os


def pytest_configure() -> None:
    os.environ.setdefault("BOT_TOKEN", "123456:TESTTOKEN")
    os.environ.setdefault("WEBHOOK_PATH_SECRET", "testsecret")
    os.environ.setdefault("PUBLIC_BASE_URL", "https://example.com")
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost:5432/x")
    os.environ.setdefault("SESSION_SECRET", "test-secret-key-at-least-32-chars-long!!")
