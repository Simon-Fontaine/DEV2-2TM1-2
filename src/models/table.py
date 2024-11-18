from enum import Enum
from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Enum as SQLEnum, Integer, CheckConstraint
from sqlalchemy.orm import relationship, mapped_column, Mapped, validates

from .base_model import BaseModel

if TYPE_CHECKING:
    from .order import Order
    from .reservation import Reservation


class TableStatus(str, Enum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    RESERVED = "Reserved"
    MAINTENANCE = "Under Maintenance"
    CLEANING = "Being Cleaned"


class Table(BaseModel):
    __tablename__ = "tables"

    __table_args__ = (
        CheckConstraint("capacity > 0", name="check_positive_capacity"),
        CheckConstraint("grid_x >= 0", name="check_grid_x_positive"),
        CheckConstraint("grid_y >= 0", name="check_grid_y_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(unique=True)
    capacity: Mapped[int]
    status: Mapped[TableStatus] = mapped_column(SQLEnum(TableStatus))
    grid_x: Mapped[int] = mapped_column(Integer, default=0)
    grid_y: Mapped[int] = mapped_column(Integer, default=0)

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

    def __repr__(self) -> str:
        return f"<Table(number={self.number}, capacity={self.capacity}, status={self.status.value}, position=({self.grid_x},{self.grid_y}))>"
