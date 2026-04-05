from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.cat import CatOrganization


class CatCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    weight_kg: Decimal | None = None
    notes: str | None = None
    organization: CatOrganization = CatOrganization.none


class CatUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    weight_kg: Decimal | None = None
    notes: str | None = None
    organization: CatOrganization | None = None


class CatOut(BaseModel):
    id: int
    user_id: int
    name: str
    weight_kg: Decimal | None
    notes: str | None
    photo_url: str | None
    organization: CatOrganization
    created_at: datetime

    model_config = {"from_attributes": True}
