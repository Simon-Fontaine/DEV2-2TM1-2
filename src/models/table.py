from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class TableStatus(Enum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    RESERVED = "Reserved"
    UNDER_MAINTENANCE = "Under Maintenance"


@dataclass
class Table:
    table_number: int
    capacity: int
    status: TableStatus = TableStatus.AVAILABLE

    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError("Capacity must be a positive integer.")

    def update_status(self, new_status: TableStatus) -> None:
        if isinstance(new_status, TableStatus):
            self.status = new_status
        else:
            raise ValueError(
                "Invalid status. Must be a value from the TableStatus enumeration."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_number": self.table_number,
            "capacity": self.capacity,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Table":
        status = TableStatus(data["status"])
        return cls(
            table_number=data["table_number"],
            capacity=data["capacity"],
            status=status,
        )

    def __str__(self) -> str:
        return f"Table {self.table_number}: Capacity {self.capacity}, Status {self.status.value}"
