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
    """
    Represents a table in a restaurant.

    Properties:
        table_number (int): The unique identifier for the table.
        capacity (int): The maximum number of people the table can accommodate.
        status (TableStatus): The current status of the table.

    Methods:
        to_dict(): Converts the Table object to a dictionary.
        from_dict(table_dict): Creates a Table object from a dictionary.
    """

    _table_number: int = field(repr=False)
    _capacity: int = field(repr=False)
    _status: TableStatus = field(default=TableStatus.AVAILABLE, repr=False)

    def __post_init__(self) -> None:
        self._validate_attributes()

    def _validate_attributes(self) -> None:
        self.table_number = self._table_number
        self.capacity = self._capacity
        self.status = self._status

    @property
    def table_number(self) -> int:
        return self._table_number

    @table_number.setter
    def table_number(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Table number must be a positive integer.")
        self._table_number = value

    @property
    def capacity(self) -> int:
        return self._capacity

    @capacity.setter
    def capacity(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Table capacity must be a positive integer.")
        self._capacity = value

    @property
    def status(self) -> TableStatus:
        return self._status

    @status.setter
    def status(self, value: TableStatus) -> None:
        if not isinstance(value, TableStatus):
            raise ValueError(
                "Invalid table status. Must be an instance of TableStatus."
            )
        self._status = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_number": self.table_number,
            "capacity": self.capacity,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, table_dict: Dict[str, Any]) -> "Table":
        return cls(
            _table_number=table_dict["table_number"],
            _capacity=table_dict["capacity"],
            _status=TableStatus(table_dict["status"]),
        )

    def __str__(self) -> str:
        return f"Table {self.table_number}: Capacity {self.capacity}, Status {self.status.value}"

    def __repr__(self) -> str:
        return f"Table(table_number={self.table_number}, capacity={self.capacity}, status={self.status})"
