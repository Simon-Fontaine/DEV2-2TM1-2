from dataclasses import dataclass
from typing import Dict, Any, List
from models.table import Table
from models.reservation import Reservation
from models.order import Order


@dataclass
class Staff:
    id: int
    name: str
    role: str
    assigned_tables: List[int] = None  # List of table numbers

    def assign_table(self, table: Table) -> None:
        if self.assigned_tables is None:
            self.assigned_tables = []
        self.assigned_tables.append(table.table_number)

    def manage_reservation(self, reservation: Reservation) -> None:
        # Logic to manage reservation
        pass

    def take_order(self, order: Order) -> None:
        # Logic to take order
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "assigned_tables": self.assigned_tables or [],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Staff":
        return cls(
            id=data["id"],
            name=data["name"],
            role=data["role"],
            assigned_tables=data.get("assigned_tables", []),
        )

    def __str__(self) -> str:
        return f"Staff {self.id}: {self.name}, Role: {self.role}"
