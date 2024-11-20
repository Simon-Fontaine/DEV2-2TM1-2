from enum import Enum
from datetime import datetime, timedelta
from typing import List, TYPE_CHECKING
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
from .base_model import BaseModel

if TYPE_CHECKING:
    from .customer import Customer
    from .table import Table


class ReservationStatus(str, Enum):
    PENDING = "Pending"  # Initial state when created
    CONFIRMED = "Confirmed"  # After staff review and confirmation
    CHECKED_IN = "Checked In"  # When customer arrives
    COMPLETED = "Completed"  # After customer leaves
    CANCELLED = "Cancelled"  # If cancelled by customer or staff
    NO_SHOW = "No Show"  # If customer doesn't show up


class ReservationPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


reservation_tables = Table(
    "reservation_tables",
    BaseModel.metadata,
    Column("reservation_id", Integer, ForeignKey("reservations.id")),
    Column("table_id", Integer, ForeignKey("tables.id")),
)


class Reservation(BaseModel):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    reservation_datetime: Mapped[datetime] = mapped_column(DateTime)
    duration: Mapped[int] = mapped_column(default=120)  # in minutes
    party_size: Mapped[int]
    status: Mapped[ReservationStatus] = mapped_column(
        SQLEnum(ReservationStatus), default=ReservationStatus.PENDING
    )
    priority: Mapped[ReservationPriority] = mapped_column(
        SQLEnum(ReservationPriority), default=ReservationPriority.MEDIUM
    )
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    special_requests: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    reminder_sent: Mapped[bool] = mapped_column(default=False)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="reservations")
    tables: Mapped[List["Table"]] = relationship(
        secondary=reservation_tables, back_populates="reservations"
    )

    @validates("party_size")
    def validate_party_size(self, key, value):
        if value <= 0:
            raise ValueError("Party size must be greater than 0")
        if value > 20:
            raise ValueError("Party size exceeds maximum capacity")
        return value

    @validates("duration")
    def validate_duration(self, key, value):
        if value < 30:
            raise ValueError("Duration must be at least 30 minutes")
        if value > 480:
            raise ValueError("Duration cannot exceed 8 hours")
        return value

    @validates("reservation_datetime")
    def validate_reservation_datetime(self, key, value):
        if value < datetime.now():
            raise ValueError("Reservation time cannot be in the past")
        return value

    def is_active(self) -> bool:
        now = datetime.now()
        end_time = self.reservation_datetime + timedelta(minutes=self.duration)
        return (
            self.status in [ReservationStatus.CONFIRMED, ReservationStatus.CHECKED_IN]
            and self.reservation_datetime <= now <= end_time
        )

    def is_upcoming(self) -> bool:
        return (
            self.status == ReservationStatus.CONFIRMED
            and self.reservation_datetime > datetime.now()
        )

    def is_late(self) -> bool:
        if self.status != ReservationStatus.CONFIRMED:
            return False
        return datetime.now() > self.reservation_datetime + timedelta(minutes=30)

    def can_cancel(self) -> bool:
        return (
            self.status in [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]
            and self.reservation_datetime > datetime.now()
        )

    def can_check_in(self) -> bool:
        now = datetime.now()
        check_in_window_start = self.reservation_datetime - timedelta(minutes=15)
        check_in_window_end = self.reservation_datetime + timedelta(minutes=30)
        return (
            self.status == ReservationStatus.CONFIRMED
            and check_in_window_start <= now <= check_in_window_end
        )

    def get_end_time(self) -> datetime:
        return self.reservation_datetime + timedelta(minutes=self.duration)

    def conflicts_with(self, other: "Reservation") -> bool:
        if not set(self.tables).intersection(set(other.tables)):
            return False

        self_end = self.get_end_time()
        other_end = other.get_end_time()

        return (
            self.reservation_datetime < other_end
            and other.reservation_datetime < self_end
        )

    def get_end_time(self) -> datetime:
        return self.reservation_datetime + timedelta(minutes=self.duration)

    def __repr__(self) -> str:
        return (
            f"<Reservation(id={self.id}, "
            f"customer={self.customer.name}, "
            f"datetime={self.reservation_datetime}, "
            f"status={self.status.value})>"
        )
