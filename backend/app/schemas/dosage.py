from decimal import Decimal

from pydantic import BaseModel, Field


class DosageRequest(BaseModel):
    drug_slug: str
    weight_kg: Decimal = Field(gt=0)
    use: str = Field(default="mid", pattern="^(min|mid|max)$")


class DosageResponse(BaseModel):
    drug: str
    weight_kg: str
    mg: str
    mg_per_kg_used: str
