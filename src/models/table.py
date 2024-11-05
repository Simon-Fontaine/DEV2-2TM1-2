from sqlalchemy import Column, Integer, Enum as SQLEnum, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates
from enum import Enum

Base = declarative_base()


class TableStatus(Enum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    RESERVED = "Reserved"
    UNDER_MAINTENANCE = "Under Maintenance"


class Table(Base):
    __tablename__ = "tables"

    table_number = Column(Integer, primary_key=True, autoincrement=True)
    capacity = Column(Integer, nullable=False)
    status = Column(SQLEnum(TableStatus), default=TableStatus.AVAILABLE, nullable=False)

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

    def __repr__(self):
        return f"<Table(table_number={self.table_number}, capacity={self.capacity}, status={self.status.value})>"
