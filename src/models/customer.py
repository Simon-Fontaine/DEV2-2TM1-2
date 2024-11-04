from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Customer:
    id: int
    name: str
    contact_info: str

    def create_reservation(self):
        # Logic to create a reservation
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "contact_info": self.contact_info,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Customer":
        return cls(
            id=data["id"],
            name=data["name"],
            contact_info=data["contact_info"],
        )

    def __str__(self) -> str:
        return f"Customer {self.id}: {self.name}"
