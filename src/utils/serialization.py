from typing import Dict, Any
from models.table import Table, TableStatus


def table_to_dict(table: Table) -> Dict[str, Any]:
    return {
        "table_number": table.table_number,
        "capacity": table.capacity,
        "status": table.status.value,
    }


def table_from_dict(data: Dict[str, Any]) -> Table:
    status = TableStatus(data["status"])
    return Table(
        table_number=data["table_number"], capacity=data["capacity"], status=status
    )
