from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy import String, DateTime
from sqlalchemy.orm import relationship, mapped_column, Mapped, validates

from .base import Base

if TYPE_CHECKING:
    from .order import Order
    from .reservation import Reservation


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(20))
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    reservations: Mapped[List["Reservation"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )

    @validates("phone")
    def validate_phone(self, key, value):
        # Basic phone validation
        if not value or len(value) < 10:
            raise ValueError("Invalid phone number")
        return value

    @validates("email")
    def validate_email(self, key, value):
        if value:  # Only validate if email is provided
            if "@" not in value or "." not in value:
                raise ValueError("Invalid email format")
        return value

    def get_active_reservations(self) -> List["Reservation"]:
        """Get all upcoming and current reservations"""
        from .reservation import ReservationStatus

        now = datetime.now()
        return [
            reservation
            for reservation in self.reservations
            if reservation.status != ReservationStatus.CANCELLED
            and reservation.reservation_datetime >= now
        ]

    def __repr__(self) -> str:
        return f"<Customer(name='{self.name}', phone='{self.phone}')>"
