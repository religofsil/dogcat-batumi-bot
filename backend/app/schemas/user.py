from datetime import datetime, time

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    telegram_id: int
    locale: str
    daily_reminder_time: time
    created_at: datetime

    model_config = {"from_attributes": True}


class LocaleUpdate(BaseModel):
    locale: str = Field(pattern="^(en|ru|ka)$")


class DailyReminderTimeUpdate(BaseModel):
    """Local wall-clock time (with app default timezone) for day-based scenario reminders."""

    daily_reminder_time: time
