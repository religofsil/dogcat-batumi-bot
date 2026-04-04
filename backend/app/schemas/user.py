from datetime import datetime

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: int
    telegram_id: int
    locale: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LocaleUpdate(BaseModel):
    locale: str = Field(pattern="^(en|ru|ka)$")
