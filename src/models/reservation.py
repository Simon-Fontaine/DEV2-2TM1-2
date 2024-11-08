from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Enum as SQLEnum,
    CheckConstraint,
    Table as AssocTable,
)
from sqlalchemy.orm import relationship, validates
from enum import Enum
from datetime import datetime
from models.base import Base


class ReservationStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"


# Association table for many-to-many relationship between Reservation and Table
reservation_table_association = AssocTable(
    "reservation_table_association",
    Base.metadata,
    Column("reservation_id", Integer, ForeignKey("reservations.id")),
    Column("table_id", Integer, ForeignKey("tables.id")),
)


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    reservation_time = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False, default=120)
    number_of_people = Column(Integer, nullable=False)
    status = Column(
        SQLEnum(ReservationStatus, native_enum=False),
        default=ReservationStatus.PENDING,
        nullable=False,
    )

    customer = relationship("Customer", back_populates="reservations")
    tables = relationship(
        "Table", secondary=reservation_table_association, back_populates="reservations"
    )

    __table_args__ = (
        CheckConstraint("number_of_people > 0", name="check_number_of_people_positive"),
        CheckConstraint("duration_minutes > 0", name="check_duration_positive"),
    )

    @validates("number_of_people")
    def validate_number_of_people(self, key, value):
        if value <= 0:
            raise ValueError("Number of people must be a positive integer.")
        return value

    @validates("reservation_time")
    def validate_reservation_time(self, key, value):
        if not isinstance(value, datetime):
            raise ValueError("Reservation time must be a datetime object.")
        if value < datetime.now():
            raise ValueError("Reservation time must be in the future.")
        return value

    @validates("duration_minutes")
    def validate_duration(self, key, value):
        if value <= 0:
            raise ValueError("Duration must be a positive integer.")
        return value

    def __repr__(self):
        table_numbers = ", ".join(str(t.table_number) for t in self.tables)
        return (
            f"<Reservation(id={self.id}, customer_id={self.customer_id}, "
            f"tables=[{table_numbers}], time={self.reservation_time}, "
            f"duration={self.duration_minutes} mins, status={self.status.value})>"
        )
