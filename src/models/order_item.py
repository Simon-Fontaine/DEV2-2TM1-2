from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class OrderItem:
    dish_name: str
    quantity: int
    price: float

    def calculate_total(self) -> float:
        return self.quantity * self.price

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dish_name": self.dish_name,
            "quantity": self.quantity,
            "price": self.price,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderItem":
        return cls(
            dish_name=data["dish_name"],
            quantity=data["quantity"],
            price=data["price"],
        )

    def __str__(self) -> str:
        return f"{self.quantity} x {self.dish_name} @ {self.price} each"
