from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ReminderOut(BaseModel):
    id: int
    cat_id: int
    scenario_run_id: int | None
    kind: str
    message_key: str
    run_at: datetime
    sent_at: datetime | None
    cancelled: bool
    payload: dict[str, Any] | None

    model_config = {"from_attributes": True}
