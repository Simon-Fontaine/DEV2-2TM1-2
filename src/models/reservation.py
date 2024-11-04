from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List


@dataclass
class Reservation:
    id: int
    customer_id: int
    table_number: int
    number_of_people: int
    reservation_time: datetime
    status_confirmed: bool = False

    def cancel(self) -> None:
        self.status_confirmed = False
        # Additional logic to release the table

    def modify(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def reschedule(self, new_time: datetime) -> None:
        self.reservation_time = new_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "table_number": self.table_number,
            "number_of_people": self.number_of_people,
            "reservation_time": self.reservation_time.isoformat(),
            "status_confirmed": self.status_confirmed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reservation":
        return cls(
            id=data["id"],
            customer_id=data["customer_id"],
            table_number=data["table_number"],
            number_of_people=data["number_of_people"],
            reservation_time=datetime.fromisoformat(data["reservation_time"]),
            status_confirmed=data["status_confirmed"],
        )

    def __str__(self) -> str:
        return (
            f"Reservation {self.id} for customer {self.customer_id} "
            f"at {self.reservation_time} on table {self.table_number}"
        )
