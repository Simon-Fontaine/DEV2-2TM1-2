from dataclasses import dataclass, field
from typing import Dict, Any, List
from models.table import Table


@dataclass
class Staff:
    """
    Represents a staff member in a restaurant.

    Properties:
        id (int): The unique identifier for the staff member.
        name (str): The name of the staff member.
        role (str): The position of the staff member.
        assigned_tables (List[int]): The tables assigned to the staff member.

    Methods:
        to_dict(): Converts the Staff object to a dictionary.
        from_dict(data): Creates a Staff object from a dictionary.
    """

    _id: int = field(repr=False)
    _name: str = field(repr=False)
    _role: str = field(repr=False)
    _assigned_tables: List[int] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self._validate_attributes()

    def _validate_attributes(self) -> None:
        self.id = self._id
        self.name = self._name
        self.role = self._role

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError("Staff ID must be a positive integer.")
        self._id = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Staff name cannot be empty.")
        self._name = value.strip()

    @property
    def role(self) -> str:
        return self._role

    @role.setter
    def role(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Staff role cannot be empty.")
        self._role = value.strip()

    @property
    def assigned_tables(self) -> List[int]:
        return self._assigned_tables

    def assign_table(self, table: Table) -> None:
        if table.table_number not in self._assigned_tables:
            self._assigned_tables.append(table.table_number)

    def unassign_table(self, table: Table) -> None:
        if table.table_number in self._assigned_tables:
            self._assigned_tables.remove(table.table_number)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "assigned_tables": self.assigned_tables,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Staff":
        return cls(
            _id=data["id"],
            _name=data["name"],
            _role=data["role"],
            _assigned_tables=data.get("assigned_tables", []),
        )

    def __str__(self):
        return f"Staff {self.id}: {self.name}, Role: {self.role}, Assigned Tables: {self.assigned_tables}"

    def __repr__(self):
        return f"Staff(id={self.id}, name='{self.name}', role='{self.role}', assigned_tables={self.assigned_tables})"
