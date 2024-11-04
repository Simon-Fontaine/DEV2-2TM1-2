from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any
from enum import Enum


class ReservationStatus(Enum):
    ACTIVE = "Active"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"


@dataclass
class Reservation:
    """
    Represents a reservation in a restaurant.

    Properties:
        id (int): The unique identifier for the reservation.
        customer_id (int): The ID of the customer making the reservation.
        table_number (int): The number of the table reserved.
        number_of_people (int): The number of people in the reservation.
        reservation_time (datetime): The date and time of the reservation.
        status (ReservationStatus): The current status of the reservation.

    Methods:
        cancel(): Cancels the reservation.
        complete(): Marks the reservation as completed.
        check_conflict(other): Checks for conflict with another reservation.
        to_dict(): Converts the Reservation object to a dictionary.
        from_dict(data): Creates a Reservation object from a dictionary.
    """

    _id: int = field(repr=False)
    _customer_id: int = field(repr=False)
    _table_number: int = field(repr=False)
    _number_of_people: int = field(repr=False)
    _reservation_time: datetime = field(repr=False)
    _status: ReservationStatus = field(default=ReservationStatus.ACTIVE, repr=False)

    RESERVATION_DURATION = timedelta(hours=2)

    def __post_init__(self):
        self._validate_attributes()

    def _validate_attributes(self):
        self.id = self._id
        self.customer_id = self._customer_id
        self.table_number = self._table_number
        self.number_of_people = self._number_of_people
        self.reservation_time = self._reservation_time
        self.status = self._status

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("ID must be a positive integer.")
        self._id = value

    @property
    def customer_id(self) -> int:
        return self._customer_id

    @customer_id.setter
    def customer_id(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Customer ID must be a positive integer.")
        self._customer_id = value

    @property
    def table_number(self) -> int:
        return self._table_number

    @table_number.setter
    def table_number(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Table number must be a positive integer.")
        self._table_number = value

    @property
    def number_of_people(self) -> int:
        return self._number_of_people

    @number_of_people.setter
    def number_of_people(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Number of people must be a positive integer.")
        self._number_of_people = value

    @property
    def reservation_time(self) -> datetime:
        return self._reservation_time

    @reservation_time.setter
    def reservation_time(self, value: datetime) -> None:
        if not isinstance(value, datetime) or value < datetime.now():
            raise ValueError("Reservation time must be a future datetime.")
        self._reservation_time = value

    @property
    def status(self) -> ReservationStatus:
        return self._status

    @status.setter
    def status(self, value: ReservationStatus) -> None:
        if not isinstance(value, ReservationStatus):
            raise ValueError("Invalid status. Must be a ReservationStatus enum.")
        self._status = value

    def cancel(self) -> None:
        self.status = ReservationStatus.CANCELLED

    def complete(self) -> None:
        self.status = ReservationStatus.COMPLETED

    def check_conflict(self, other: "Reservation") -> bool:
        if self.table_number != other.table_number:
            return False
        return (
            abs(self.reservation_time - other.reservation_time)
            < self.RESERVATION_DURATION
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "table_number": self.table_number,
            "number_of_people": self.number_of_people,
            "reservation_time": self.reservation_time.isoformat(),
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reservation":
        return cls(
            _id=data["id"],
            _customer_id=data["customer_id"],
            _table_number=data["table_number"],
            _number_of_people=data["number_of_people"],
            _reservation_time=datetime.fromisoformat(data["reservation_time"]),
            _status=ReservationStatus(data.get("status", "active")),
        )

    def __str__(self) -> str:
        return (
            f"Reservation {self.id} for customer {self.customer_id} "
            f"at {self.reservation_time} on table {self.table_number} "
            f"(Status: {self.status.value})"
        )

    def __repr__(self) -> str:
        return (
            f"Reservation(id={self.id}, customer_id={self.customer_id}, "
            f"table_number={self.table_number}, number_of_people={self.number_of_people}, "
            f"reservation_time={self.reservation_time}, status={self.status})"
        )
