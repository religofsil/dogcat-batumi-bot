from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cat import Cat
    from app.models.reminder import Reminder


class ScenarioType(StrEnum):
    new_capture = "new_capture"
    adopted_home = "adopted_home"
    post_prep = "post_prep"
    potential_adopter = "potential_adopter"
    sterilization = "sterilization"


class ScenarioStatus(StrEnum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cat_id: Mapped[int] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"), index=True)
    scenario_type: Mapped[ScenarioType] = mapped_column(
        Enum(ScenarioType, name="scenario_type_enum", native_enum=False, length=32)
    )
    status: Mapped[ScenarioStatus] = mapped_column(
        Enum(ScenarioStatus, name="scenario_status_enum", native_enum=False, length=32),
        default=ScenarioStatus.active,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    context: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    cat: Mapped["Cat"] = relationship(back_populates="scenario_runs")
    reminders: Mapped[list["Reminder"]] = relationship(back_populates="scenario_run")
