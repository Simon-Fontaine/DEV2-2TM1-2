import logging
import json
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

    # -------------------- Table Methods --------------------

    def add_table(self, table: Table) -> None:
        if table.table_number in self.tables:
            raise ValueError(f"Table {table.table_number} already exists.")
        self.tables[table.table_number] = table
        logging.info(f"Table {table.table_number} added.")

    def delete_table(self, table_number: int) -> None:
        if table_number in self.tables:
            del self.tables[table_number]
            logging.info(f"Table {table_number} deleted.")
        else:
            raise ValueError(f"Table {table_number} not found.")

    def update_table(
        self,
        table_number: int,
        new_capacity: Optional[int] = None,
        new_status: Optional[TableStatus] = None,
    ) -> None:
        table = self.tables.get(table_number)
        if table:
            if new_capacity is not None:
                if new_capacity > 0:
                    table.capacity = new_capacity
                else:
                    raise ValueError("Capacity must be a positive integer.")
            if new_status is not None:
                table.update_status(new_status)
            logging.info(f"Table {table_number} updated.")
        else:
            raise ValueError(f"Table {table_number} not found.")

    def list_tables(self) -> None:
        if not self.tables:
            logging.info("No tables available.")
        else:
            for table in self.tables.values():
                print(table)

    def merge_tables(self, table_numbers: List[int]) -> None:
        # Check if all tables exist
        if not all(num in self.tables for num in table_numbers):
            raise ValueError("One or more tables do not exist.")
        # Calculate new capacity
        new_capacity = sum(self.tables[num].capacity for num in table_numbers)
        # Create new table with a unique table number
        new_table_number = max(self.tables.keys()) + 1
        merged_table = Table(table_number=new_table_number, capacity=new_capacity)
        # Remove old tables
        for num in table_numbers:
            del self.tables[num]
        # Add merged table
        self.tables[new_table_number] = merged_table
        logging.info(f"Merged tables {table_numbers} into table {new_table_number}.")

    # -------------------- Reservation Methods --------------------

    def add_reservation(self, reservation: Reservation) -> None:
        if reservation.id in self.reservations:
            raise ValueError(f"Reservation {reservation.id} already exists.")
        if reservation.table_number not in self.tables:
            raise ValueError(f"Table {reservation.table_number} does not exist.")
        if reservation.customer_id not in self.customers:
            raise ValueError(f"Customer {reservation.customer_id} does not exist.")
        self.reservations[reservation.id] = reservation
        logging.info(f"Reservation {reservation.id} added.")

    def cancel_reservation(self, reservation_id: int) -> None:
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            raise ValueError(f"Reservation {reservation_id} not found.")
        reservation.cancel()
        logging.info(f"Reservation {reservation_id} canceled.")

    def modify_reservation(self, reservation_id: int, **kwargs) -> None:
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            raise ValueError(f"Reservation {reservation_id} not found.")
        reservation.modify(**kwargs)
        logging.info(f"Reservation {reservation_id} modified.")

    def reschedule_reservation(self, reservation_id: int, new_time) -> None:
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            raise ValueError(f"Reservation {reservation_id} not found.")
        reservation.reschedule(new_time)
        logging.info(f"Reservation {reservation_id} rescheduled to {new_time}.")

    # -------------------- Order Methods --------------------

    def add_order(self, order: Order) -> None:
        if order.id in self.orders:
            raise ValueError(f"Order {order.id} already exists.")
        if order.table_number not in self.tables:
            raise ValueError(f"Table {order.table_number} does not exist.")
        self.orders[order.id] = order
        logging.info(f"Order {order.id} added.")

    def modify_order(self, order_id: int, **kwargs) -> None:
        order = self.orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found.")
        order.modify_order(**kwargs)
        logging.info(f"Order {order_id} modified.")

    def delete_order(self, order_id: int) -> None:
        if order_id not in self.orders:
            raise ValueError(f"Order {order_id} not found.")
        del self.orders[order_id]
        logging.info(f"Order {order_id} deleted.")

    # -------------------- Staff Methods --------------------

    def add_staff_member(self, staff: Staff) -> None:
        if staff.id in self.staff_members:
            raise ValueError(f"Staff member {staff.id} already exists.")
        self.staff_members[staff.id] = staff
        logging.info(f"Staff member {staff.id} added.")

    def assign_table_to_staff(self, staff_id: int, table_number: int) -> None:
        staff = self.staff_members.get(staff_id)
        table = self.tables.get(table_number)
        if not staff:
            raise ValueError(f"Staff member {staff_id} not found.")
        if not table:
            raise ValueError(f"Table {table_number} does not exist.")
        staff.assign_table(table)
        logging.info(f"Table {table_number} assigned to staff member {staff_id}.")

    def manage_reservation(self, staff_id: int, reservation_id: int) -> None:
        staff = self.staff_members.get(staff_id)
        reservation = self.reservations.get(reservation_id)
        if not staff:
            raise ValueError(f"Staff member {staff_id} not found.")
        if not reservation:
            raise ValueError(f"Reservation {reservation_id} not found.")
        staff.manage_reservation(reservation)
        logging.info(
            f"Reservation {reservation_id} managed by staff member {staff_id}."
        )

    # -------------------- Customer Methods --------------------

    def add_customer(self, customer: Customer) -> None:
        if customer.id in self.customers:
            raise ValueError(f"Customer {customer.id} already exists.")
        self.customers[customer.id] = customer
        logging.info(f"Customer {customer.id} added.")

    # -------------------- Serialization Methods --------------------

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
        restaurant = cls(
            name=data.get("name", "Unnamed Restaurant"),
            location=data.get("location", "Unknown"),
        )
        # Deserialize tables
        for table_data in data.get("tables", []):
            table = Table.from_dict(table_data)
            restaurant.tables[table.table_number] = table
        # Deserialize reservations
        for res_data in data.get("reservations", []):
            reservation = Reservation.from_dict(res_data)
            restaurant.reservations[reservation.id] = reservation
        # Deserialize orders
        for order_data in data.get("orders", []):
            order = Order.from_dict(order_data)
            restaurant.orders[order.id] = order
        # Deserialize staff members
        for staff_data in data.get("staff_members", []):
            staff = Staff.from_dict(staff_data)
            restaurant.staff_members[staff.id] = staff
        # Deserialize customers
        for customer_data in data.get("customers", []):
            customer = Customer.from_dict(customer_data)
            restaurant.customers[customer.id] = customer
        return restaurant

    def save_state(self, filename: str) -> None:
        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(self.to_dict(), file, ensure_ascii=False, indent=2)
            logging.debug(f"Restaurant state saved to {filename}.")
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
            return cls(name="Default Restaurant", location="Unknown")
        except Exception as e:
            logging.error(f"Error loading state: {e}")
            return cls(name="Default Restaurant", location="Unknown")
