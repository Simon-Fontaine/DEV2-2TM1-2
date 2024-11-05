from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class OrderItem:
    """
    Represents an item in an order.

    Properties:
        dish_name (str): The name of the dish.
        quantity (int): The quantity of the dish.
        price (float): The price of the dish.
        total (float): The total cost of the ordered items.

    Methods:
        to_dict(): Converts the OrderItem object to a dictionary.
        from_dict(data): Creates an OrderItem object from a dictionary.
    """

    _dish_name: str = field(repr=False)
    _quantity: int = field(repr=False)
    _price: float = field(repr=False)

    def __post_init__(self) -> None:
        self._validate_attributes()

    def _validate_attributes(self) -> None:
        self.dish_name = self._dish_name
        self.quantity = self._quantity
        self.price = self._price

    @property
    def dish_name(self) -> str:
        return self._dish_name

    @dish_name.setter
    def dish_name(self, value: str) -> None:
        if not value or not isinstance(value, str):
            raise ValueError("Dish name must be a non-empty string.")
        self._dish_name = value

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Quantity must be a positive integer.")
        self._quantity = value

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError("Price must be a non-negative number.")
        self._price = float(value)

    @property
    def total(self) -> float:
        return self.quantity * self.price

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dish_name": self.dish_name,
            "quantity": self.quantity,
            "price": self.price,
            "total": self.total,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrderItem":
        return cls(
            _dish_name=data["dish_name"],
            _quantity=data["quantity"],
            _price=data["price"],
        )

    def __str__(self) -> str:
        return f"{self.dish_name} x {self.quantity} = ${self.total:.2f} (${self.price:.2f} each)"

    def __repr__(self) -> str:
        return f"OrderItem(dish_name='{self.dish_name}', quantity={self.quantity}, price={self.price})"
