from commands.command import Command
from models.restaurant import Restaurant
from models.table import Table, TableStatus
from typing import Optional


class AddTableCommand(Command):

    def __init__(
        self,
        restaurant: Restaurant,
        table_number: int,
        capacity: int,
        status: TableStatus,
    ):
        self.restaurant = restaurant
        self.table_number = table_number
        self.capacity = capacity
        self.status = status

    def execute(self) -> None:
        table = Table(
            table_number=self.table_number,
            capacity=self.capacity,
            status=self.status,
        )
        self.restaurant.add_table(table)


class DeleteTableCommand(Command):

    def __init__(self, restaurant: Restaurant, table_number: int):
        self.restaurant = restaurant
        self.table_number = table_number

    def execute(self) -> None:
        self.restaurant.delete_table(self.table_number)


class UpdateTableCommand(Command):

    def __init__(
        self,
        restaurant: Restaurant,
        table_number: int,
        new_capacity: Optional[int] = None,
        new_status: Optional[TableStatus] = None,
    ):
        self.restaurant = restaurant
        self.table_number = table_number
        self.new_capacity = new_capacity
        self.new_status = new_status

    def execute(self) -> None:
        self.restaurant.update_table(
            table_number=self.table_number,
            new_capacity=self.new_capacity,
            new_status=self.new_status,
        )


class ListTablesCommand(Command):

    def __init__(self, restaurant: Restaurant):
        self.restaurant = restaurant

    def execute(self) -> None:
        self.restaurant.list_tables()
