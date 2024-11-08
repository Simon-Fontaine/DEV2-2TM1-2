from sqlalchemy import Column, Integer, Enum as SQLEnum, CheckConstraint, String
from sqlalchemy.orm import relationship, validates, object_session
from enum import Enum
from datetime import datetime
from sqlalchemy import func, cast, String as SQLString
from models.base import Base
from models.reservation import Reservation, ReservationStatus


class TableStatus(Enum):
    AVAILABLE = "Available"
    RESERVED = "Reserved"
    OCCUPIED = "Occupied"
    UNDER_MAINTENANCE = "Under Maintenance"


class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_number = Column(Integer, unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    status = Column(
        SQLEnum(TableStatus, native_enum=False),
        default=TableStatus.AVAILABLE,
        nullable=False,
    )

    reservations = relationship(
        "Reservation",
        secondary="reservation_table_association",
        back_populates="tables",
    )

    orders = relationship("Order", back_populates="table", cascade="all, delete-orphan")

    __table_args__ = (CheckConstraint("capacity > 0", name="check_capacity_positive"),)

    @validates("capacity")
    def validate_capacity(self, key, value):
        if value <= 0:
            raise ValueError("Table capacity must be a positive integer.")
        return value

    @validates("status")
    def validate_status(self, key, value):
        if not isinstance(value, TableStatus):
            raise ValueError(
                "Invalid table status. Must be an instance of TableStatus."
            )
        return value

    @property
    def current_status(self) -> TableStatus:
        """Calculate the current status of the table based on active reservations and manual status."""
        session = object_session(self)
        if not session:
            return self.status  # If no session, return stored status

        now = datetime.now()

        # If the table is under maintenance or occupied, return its manual status
        if self.status in [TableStatus.UNDER_MAINTENANCE, TableStatus.OCCUPIED]:
            return self.status

        # Prepare duration string for SQLAlchemy datetime arithmetic
        duration_str = cast(Reservation.duration_minutes, String) + " minutes"

        # Calculate reservation end time within the query
        reservation_end = func.datetime(Reservation.reservation_time, duration_str)

        # Count active reservations
        active_reservations = (
            session.query(Reservation)
            .filter(
                Reservation.tables.contains(self),
                Reservation.status == ReservationStatus.CONFIRMED,
                Reservation.reservation_time <= now,
                reservation_end > now,
            )
            .count()
        )

        if active_reservations > 0:
            return TableStatus.RESERVED
        else:
            return TableStatus.AVAILABLE

    def __repr__(self):
        return (
            f"<Table(id={self.id}, table_number={self.table_number}, "
            f"capacity={self.capacity}, status={self.current_status.value})>"
        )
