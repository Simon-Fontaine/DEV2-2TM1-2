from enum import Enum
from typing import Dict, Any


class TableStatus(Enum):

    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    RESERVED = "Reserved"
    UNDER_MAINTENANCE = "Under Maintenance"


class Table:

    def __init__(
        self,
        table_number: int,
        capacity: int,
        status: TableStatus = TableStatus.AVAILABLE,
    ) -> None:
        if capacity <= 0:
            raise ValueError("La capacité doit être un entier positif.")
        self.table_number: int = table_number
        self.capacity: int = capacity
        self.status: TableStatus = status

    def update_status(self, new_status: TableStatus) -> None:
        if isinstance(new_status, TableStatus):
            self.status = new_status
        else:
            raise ValueError(
                "Statut invalide. Doit être une valeur de l'énumération TableStatus."
            )

    def __str__(self) -> str:
        return f"Table {self.table_number}: Capacité {self.capacity}, Statut {self.status.value}"
