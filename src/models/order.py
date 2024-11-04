from dataclasses import dataclass, field
from typing import Dict, Any, List
from models.order_item import OrderItem


@dataclass
class Order:
    id: int
    table_number: int
    items: List[OrderItem] = field(default_factory=list)
    preparation_status: str = "Pending"

    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)

    def modify_order(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "table_number": self.table_number,
            "preparation_status": self.preparation_status,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        items = [OrderItem.from_dict(item) for item in data.get("items", [])]
        return cls(
            id=data["id"],
            table_number=data["table_number"],
            items=items,
            preparation_status=data.get("preparation_status", "Pending"),
        )

    def __str__(self) -> str:
        items_str = "\n".join([str(item) for item in self.items])
        return (
            f"Order {self.id} for table {self.table_number}:\n"
            f"{items_str}\nStatus: {self.preparation_status}"
        )
