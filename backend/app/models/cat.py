from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.reminder import Reminder
    from app.models.scenario import ScenarioRun
    from app.models.user import User


class CatOrganization(StrEnum):
    catebi = "catebi"
    dogcat_batumi = "dogcat_batumi"
    dogcat_tbilisi = "dogcat_tbilisi"
    none = "none"


class Cat(Base):
    __tablename__ = "cats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    organization: Mapped[CatOrganization] = mapped_column(
        Enum(CatOrganization, name="cat_organization_enum", native_enum=False, length=32),
        default=CatOrganization.none,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="cats")
    scenario_runs: Mapped[list["ScenarioRun"]] = relationship(
        back_populates="cat", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        back_populates="cat", cascade="all, delete-orphan"
    )
