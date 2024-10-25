from enum import Enum


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
    ):
        self.table_number = table_number
        self.capacity = capacity
        self.status = status

    def update_status(self, new_status: TableStatus):
        self.status = new_status
