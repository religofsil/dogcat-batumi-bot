from datetime import datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.cat import Cat


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    locale: Mapped[str] = mapped_column(String(8), default="en")
    daily_reminder_time: Mapped[time] = mapped_column(Time(), default=time(9, 0))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cats: Mapped[list["Cat"]] = relationship(back_populates="user", cascade="all, delete-orphan")
