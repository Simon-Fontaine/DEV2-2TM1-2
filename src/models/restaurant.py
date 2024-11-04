import json
import logging
from typing import Dict, List, Any, Optional
from models.table import Table, TableStatus
from models.reservation import Reservation
from models.order import Order
from models.customer import Customer
from models.staff import Staff


class Restaurant:

    def __init__(self, name: str, location: str) -> None:
        self.name = name
        self.location = location
        self.tables: Dict[int, Table] = {}
        self.reservations: Dict[int, Reservation] = {}
        self.orders: Dict[int, Order] = {}
        self.staff_members: Dict[int, Staff] = {}
        self.customers: Dict[int, Customer] = {}

    # Table Management Methods
    def add_table(self, table: Table) -> None:
        """Add a new table to the restaurant."""
        if table.table_number in self.tables:
            raise ValueError(f"Table {table.table_number} already exists.")
        self.tables[table.table_number] = table

    def delete_table(self, table_number: int) -> None:
        """Delete a table from the restaurant."""
        if table_number not in self.tables:
            raise ValueError(f"Table {table_number} does not exist.")
        del self.tables[table_number]

    def update_table(
        self,
        table_number: int,
        new_capacity: Optional[int] = None,
        new_status: Optional[TableStatus] = None,
    ) -> None:
        """Update the capacity or status of a table."""
        table = self.tables.get(table_number)
        if not table:
            raise ValueError(f"Table {table_number} does not exist.")
        if new_capacity is not None:
            table.capacity = new_capacity
        if new_status is not None:
            table.status = new_status

    def get_table(self, table_number: int) -> Optional[Table]:
        """Get a table by its number."""
        return self.tables.get(table_number)

    def list_tables(self) -> List[Table]:
        """List all tables in the restaurant."""
        return list(self.tables.values())

    def merge_tables(self, table_numbers: List[int]) -> None:
        """Merge multiple tables into a single table."""
        if not all(num in self.tables for num in table_numbers):
            raise ValueError("One or more tables do not exist.")
        new_capacity = sum(self.tables[num].capacity for num in table_numbers)
        new_table_number = max(self.tables.keys()) + 1
        merged_table = Table(_table_number=new_table_number, _capacity=new_capacity)
        for num in table_numbers:
            del self.tables[num]
        self.tables[new_table_number] = merged_table

    def split_table(self, table_number: int, new_capacities: List[int]) -> None:
        """Split a table into multiple smaller tables."""
        if table_number not in self.tables:
            raise ValueError(f"Table {table_number} does not exist.")
        original_table = self.tables[table_number]
        if sum(new_capacities) != original_table.capacity:
            raise ValueError(
                "Sum of new capacities must equal the original table capacity."
            )
        del self.tables[table_number]
        for i, capacity in enumerate(new_capacities, 1):
            new_table_number = max(self.tables.keys()) + 1
            new_table = Table(_table_number=new_table_number, _capacity=capacity)
            self.tables[new_table_number] = new_table

    # Reservation Management Methods
    def add_reservation(self, new_reservation: Reservation) -> None:
        """Add a new reservation to the restaurant."""
        if new_reservation.customer_id not in self.customers:
            raise ValueError(f"Customer {new_reservation.customer_id} does not exist.")
        if new_reservation.table_number not in self.tables:
            raise ValueError(f"Table {new_reservation.table_number} does not exist.")
        if new_reservation.id in self.reservations:
            raise ValueError(f"Reservation {new_reservation.id} already exists.")
        if any(new_reservation.check_conflict(r) for r in self.reservations.values()):
            raise ValueError("Reservation conflicts with an existing reservation.")
        self.reservations[new_reservation.id] = new_reservation

    def cancel_reservation(self, reservation_id: int) -> None:
        """Cancel a reservation."""
        if reservation_id not in self.reservations:
            raise ValueError(f"Reservation {reservation_id} does not exist.")
        del self.reservations[reservation_id]

    def get_reservation(self, reservation_id: int) -> Optional[Reservation]:
        """Get a reservation by its ID."""
        return self.reservations.get(reservation_id)

    def list_reservations(self) -> List[Reservation]:
        """List all reservations."""
        return list(self.reservations.values())

    def update_reservation(self, reservation_id: int, **kwargs) -> None:
        """Update a reservation's details."""
        if reservation_id not in self.reservations:
            raise ValueError(f"Reservation {reservation_id} does not exist.")
        reservation = self.reservations[reservation_id]
        for key, value in kwargs.items():
            if hasattr(reservation, key):
                setattr(reservation, key, value)
            else:
                raise ValueError(f"Invalid attribute: {key}")

    # Staff Management Methods
    def add_staff(self, staff: Staff) -> None:
        """Add a new staff member."""
        if staff.id in self.staff_members:
            raise ValueError(f"Staff member with ID {staff.id} already exists.")
        self.staff_members[staff.id] = staff

    def remove_staff(self, staff_id: int) -> None:
        """Remove a staff member."""
        if staff_id not in self.staff_members:
            raise ValueError(f"Staff member with ID {staff_id} does not exist.")
        del self.staff_members[staff_id]

    def get_staff(self, staff_id: int) -> Optional[Staff]:
        """Get a staff member by their ID."""
        return self.staff_members.get(staff_id)

    def list_staff(self) -> List[Staff]:
        """List all staff members."""
        return list(self.staff_members.values())

    def update_staff(self, staff_id: int, **kwargs) -> None:
        """Update a staff member's details."""
        if staff_id not in self.staff_members:
            raise ValueError(f"Staff member with ID {staff_id} does not exist.")
        staff = self.staff_members[staff_id]
        for key, value in kwargs.items():
            if hasattr(staff, key):
                setattr(staff, key, value)
            else:
                raise ValueError(f"Invalid attribute: {key}")

    # Customer Management Methods
    def add_customer(self, customer: Customer) -> None:
        """Add a new customer."""
        if customer.id in self.customers:
            raise ValueError(f"Customer with ID {customer.id} already exists.")
        self.customers[customer.id] = customer

    def remove_customer(self, customer_id: int) -> None:
        """Remove a customer."""
        if customer_id not in self.customers:
            raise ValueError(f"Customer with ID {customer_id} does not exist.")
        del self.customers[customer_id]

    def get_customer(self, customer_id: int) -> Optional[Customer]:
        """Get a customer by their ID."""
        return self.customers.get(customer_id)

    def list_customers(self) -> List[Customer]:
        """List all customers."""
        return list(self.customers.values())

    def update_customer(self, customer_id: int, **kwargs) -> None:
        """Update a customer's details."""
        if customer_id not in self.customers:
            raise ValueError(f"Customer with ID {customer_id} does not exist.")
        customer = self.customers[customer_id]
        for key, value in kwargs.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
            else:
                raise ValueError(f"Invalid attribute: {key}")

    # Order Management Methods
    def add_order(self, order: Order) -> None:
        """Add a new order."""
        if order.id in self.orders:
            raise ValueError(f"Order with ID {order.id} already exists.")
        self.orders[order.id] = order

    def remove_order(self, order_id: int) -> None:
        """Remove an order."""
        if order_id not in self.orders:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        del self.orders[order_id]

    def get_order(self, order_id: int) -> Optional[Order]:
        """Get an order by its ID."""
        return self.orders.get(order_id)

    def list_orders(self) -> List[Order]:
        """List all orders."""
        return list(self.orders.values())

    def update_order_status(self, order_id: int, new_status: str) -> None:
        """Update the status of an order."""
        if order_id not in self.orders:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        self.orders[order_id].status = new_status

    def update_order(self, order_id: int, **kwargs) -> None:
        """Update an order's details."""
        if order_id not in self.orders:
            raise ValueError(f"Order with ID {order_id} does not exist.")
        order = self.orders[order_id]
        for key, value in kwargs.items():
            if hasattr(order, key):
                setattr(order, key, value)
            else:
                raise ValueError(f"Invalid attribute: {key}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "location": self.location,
            "tables": [table.to_dict() for table in self.tables.values()],
            "reservations": [res.to_dict() for res in self.reservations.values()],
            "orders": [order.to_dict() for order in self.orders.values()],
            "staff_members": [staff.to_dict() for staff in self.staff_members.values()],
            "customers": [customer.to_dict() for customer in self.customers.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Restaurant":
        restaurant = cls(data["name"], data["location"])
        restaurant.tables = {
            t["table_number"]: Table.from_dict(t) for t in data["tables"]
        }
        restaurant.reservations = {
            r["id"]: Reservation.from_dict(r) for r in data["reservations"]
        }
        restaurant.orders = {o["id"]: Order.from_dict(o) for o in data["orders"]}
        restaurant.staff_members = {
            s["id"]: Staff.from_dict(s) for s in data["staff_members"]
        }
        restaurant.customers = {
            c["id"]: Customer.from_dict(c) for c in data["customers"]
        }
        return restaurant

    def save_state(self, filename: str) -> None:
        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(self.to_dict(), file, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving state: {e}")

    @classmethod
    def load_state(cls, filename: str) -> "Restaurant":
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
                return cls.from_dict(data)
        except FileNotFoundError:
            logging.warning(f"File {filename} not found. Creating a new restaurant.")
            return cls("Default Restaurant", "Unknown")
        except Exception as e:
            logging.error(f"Error loading state: {e}")
            return cls("Default Restaurant", "Unknown")
