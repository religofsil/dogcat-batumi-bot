from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CatCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    weight_kg: Decimal | None = None
    notes: str | None = None


class CatUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    weight_kg: Decimal | None = None
    notes: str | None = None


class CatOut(BaseModel):
    id: int
    user_id: int
    name: str
    weight_kg: Decimal | None
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
