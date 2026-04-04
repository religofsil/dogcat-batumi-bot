from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cat import Cat
    from app.models.scenario import ScenarioRun


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cat_id: Mapped[int] = mapped_column(ForeignKey("cats.id", ondelete="CASCADE"), index=True)
    scenario_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenario_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(64), index=True)
    message_key: Mapped[str] = mapped_column(String(128))
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    cat: Mapped["Cat"] = relationship(back_populates="reminders")
    scenario_run: Mapped["ScenarioRun | None"] = relationship(back_populates="reminders")
