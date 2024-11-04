from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List
from models.order_item import OrderItem


class OrderStatus(Enum):
    PENDING = "Pending"
    PREPARATION = "Preparation"
    SERVED = "Served"
    CANCELLED = "Cancelled"


@dataclass
class Order:
    """
    Represents an order in a restaurant.

    Properties:
        id (int): The unique identifier for the order.
        table_number (int): The number of the table for the order.
        staff_id (int): The ID of the staff member handling the order.
        status (OrderStatus): The current status of the order.
        items (List[OrderItem]): The list of items in the order.

    Methods:
        add_item(item): Adds an item to the order.
        remove_item(item_id): Removes an item from the order.
        calculate_total(): Calculates the total price of the order.
        to_dict(): Converts the Order object to a dictionary.
        from_dict(data): Creates an Order object from a dictionary.
    """

    _id: int = field(repr=False)
    _table_number: int = field(repr=False)
    _items: List[OrderItem] = field(default_factory=list, repr=False)
    _status: OrderStatus = field(default=OrderStatus.PENDING, repr=False)

    def __post_init__(self) -> None:
        self._validate_attributes()

    def _validate_attributes(self) -> None:
        self.id = self._id
        self.table_number = self._table_number
        self.status = self._status
        self.items = self._items

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Order ID must be a positive integer.")
        self._id = value

    @property
    def table_number(self) -> int:
        return self._table_number

    @table_number.setter
    def table_number(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Table number must be a positive integer.")
        self._table_number = value

    @property
    def items(self) -> List[OrderItem]:
        return self._items

    @items.setter
    def items(self, value: List[OrderItem]) -> None:
        if not all(isinstance(item, OrderItem) for item in value):
            raise ValueError("All order items must be instances of OrderItem.")
        self._items = value

    @property
    def status(self) -> OrderStatus:
        return self._status

    @status.setter
    def status(self, value: OrderStatus) -> None:
        if not isinstance(value, OrderStatus):
            raise ValueError("Status must be an instance of OrderStatus.")
        self._status = value

    def add_item(self, item: OrderItem) -> None:
        if not isinstance(item, OrderItem):
            raise ValueError("Item must be an instance of OrderItem.")
        self._items.append(item)

    def remove_item(self, item_id: int) -> None:
        self._items = [item for item in self._items if item.id != item_id]

    def update_status(self, new_status: OrderStatus) -> None:
        self.status = new_status

    @property
    def total(self) -> float:
        return sum(item.total for item in self._items)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "table_number": self.table_number,
            "items": [item.to_dict() for item in self.items],
            "status": self.status.value,
            "total": self.total,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        items = [OrderItem.from_dict(item_data) for item_data in data.get("items", [])]
        return cls(
            _id=data["id"],
            _table_number=data["table_number"],
            _items=items,
            _status=OrderStatus(data["status"]),
        )

    def __str__(self) -> str:
        items_str = "\n".join(str(item) for item in self.items)
        return (
            f"Order {self.id} for table {self.table_number}:\n"
            f"Status: {self.status.value}\n"
            f"Items:\n{items_str}\n"
            f"Total: ${self.total:.2f}"
        )

    def __repr__(self) -> str:
        return f"Order(id={self.id}, table_number={self.table_number}, items={self.items}, status={self.status})"
