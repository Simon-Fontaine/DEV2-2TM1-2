from dataclasses import dataclass, field
from typing import Dict, Any
import re


@dataclass
class Customer:
    """
    Represents a customer in a restaurant.

    Properties:
        id (int): The unique identifier for the customer.
        name (str): The name of the customer.
        contact_info (str): The contact information of the customer.

    Methods:
        to_dict(): Converts the Customer object to a dictionary.
        from_dict(data): Creates a Customer object from a dictionary.
    """

    _id: int = field(repr=False)
    _name: str = field(repr=False)
    _contact_info: str = field(repr=False)

    def __post_init__(self) -> None:
        self._validate_attributes()

    def _validate_attributes(self) -> None:
        self.id = self._id
        self.name = self._name
        self.contact_info = self._contact_info

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Customer ID must be a positive integer.")
        self._id = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value or not isinstance(value, str):
            raise ValueError("Name must be a non-empty string.")
        self._name = value

    @property
    def contact_info(self) -> str:
        return self._contact_info

    @contact_info.setter
    def contact_info(self, value: str) -> None:
        if not self._validate_contact_info(value):
            raise ValueError("Invalid contact information.")
        self._contact_info = value

    @staticmethod
    def _validate_contact_info(contact_info: str) -> bool:
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        phone_pattern = r"^\+?1?\d{9,15}$"
        return (
            re.match(email_pattern, contact_info) is not None
            or re.match(phone_pattern, contact_info) is not None
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "contact_info": self.contact_info,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Customer":
        return cls(
            _id=data["id"],
            _name=data["name"],
            _contact_info=data["contact_info"],
        )

    def __str__(self) -> str:
        return (
            f"Customer {self.id}: Name {self.name}, "
            f"Contact Info {self.contact_info}"
        )

    def __repr__(self) -> str:
        return f"Customer(id={self.id}, name='{self.name}', contact_info='{self.contact_info}')"
