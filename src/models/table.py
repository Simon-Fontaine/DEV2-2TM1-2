from enum import Enum
from typing import List, TYPE_CHECKING
from datetime import datetime, timedelta
from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import relationship, mapped_column, Mapped, validates

from .base import Base

if TYPE_CHECKING:
    from .order import Order
    from .reservation import Reservation


class TableStatus(str, Enum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    RESERVED = "Reserved"
    MAINTENANCE = "Under Maintenance"
    CLEANING = "Being Cleaned"


class Table(Base):
    __tablename__ = "tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(unique=True)
    capacity: Mapped[int]
    status: Mapped[TableStatus] = mapped_column(SQLEnum(TableStatus))
    location: Mapped[str] = mapped_column(String(50))

    # Relationships
    orders: Mapped[List["Order"]] = relationship(
        back_populates="table", cascade="all, delete-orphan"
    )
    reservations: Mapped[List["Reservation"]] = relationship(
        secondary="reservation_tables", back_populates="tables"
    )

    @validates("capacity")
    def validate_capacity(self, key, value):
        if value <= 0:
            raise ValueError("Table capacity must be greater than 0")
        return value

    @validates("number")
    def validate_number(self, key, value):
        if value <= 0:
            raise ValueError("Table number must be greater than 0")
        return value

    def is_available_at(
        self, start_time: datetime, duration_minutes: int = 120
    ) -> bool:
        """Check if table is available at a specific time"""
        from .reservation import ReservationStatus

        end_time = start_time + timedelta(minutes=duration_minutes)
        return not any(
            r.reservation_datetime <= end_time
            and (r.reservation_datetime + timedelta(minutes=r.duration)) >= start_time
            for r in self.reservations
            if r.status != ReservationStatus.CANCELLED
        )

    def __repr__(self) -> str:
        return f"<Table(number={self.number}, capacity={self.capacity}, status={self.status.value})>"
