from enum import Enum
from typing import List, TYPE_CHECKING
from datetime import datetime, timedelta
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Table,
    Enum as SQLEnum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, mapped_column, Mapped, validates

from .base import Base

if TYPE_CHECKING:
    from .customer import Customer
    from .table import Table


class ReservationStatus(str, Enum):
    CONFIRMED = "Confirmed"
    SEATED = "Seated"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"


# Association tables
reservation_tables = Table(
    "reservation_tables",
    Base.metadata,
    Column("reservation_id", Integer, ForeignKey("reservations.id")),
    Column("table_id", Integer, ForeignKey("tables.id")),
)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    reservation_datetime: Mapped[datetime] = mapped_column(DateTime)
    duration: Mapped[int] = mapped_column(default=120)  # in minutes
    party_size: Mapped[int]
    status: Mapped[ReservationStatus] = mapped_column(
        SQLEnum(ReservationStatus), default=ReservationStatus.CONFIRMED
    )
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="reservations")
    tables: Mapped[List["Table"]] = relationship(
        secondary=reservation_tables, back_populates="reservations"
    )

    @validates("party_size")
    def validate_party_size(self, key, value):
        if value <= 0:
            raise ValueError("Party size must be greater than 0")
        return value

    @validates("duration")
    def validate_duration(self, key, value):
        if value < 30:  # Minimum 30 minutes
            raise ValueError("Duration must be at least 30 minutes")
        return value

    def is_active(self) -> bool:
        """Check if the reservation is currently active"""
        now = datetime.now()
        return (
            self.status == ReservationStatus.CONFIRMED
            and self.reservation_datetime
            <= now
            <= self.reservation_datetime + timedelta(minutes=self.duration)
        )

    def __repr__(self) -> str:
        return f"<Reservation(datetime={self.reservation_datetime}, party_size={self.party_size}, status={self.status.value})>"
