from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.scenario import ScenarioStatus, ScenarioType


class ScenarioStartRequest(BaseModel):
    scenario_type: ScenarioType
    anchor_at: datetime | None = None
    context: dict[str, Any] | None = None


class ScenarioOut(BaseModel):
    id: int
    cat_id: int
    scenario_type: ScenarioType
    status: ScenarioStatus
    started_at: datetime
    context: dict[str, Any] | None

    model_config = {"from_attributes": True}
