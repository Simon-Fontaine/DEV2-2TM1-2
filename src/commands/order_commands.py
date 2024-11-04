from commands.command import Command
from models.restaurant import Restaurant
from models.order import Order
from models.order_item import OrderItem
import logging


class AddOrderCommand(Command):

    def __init__(
        self,
        restaurant: Restaurant,
        order_id: int,
        table_number: int,
        items_data: list,
    ):
        self.restaurant = restaurant
        self.order_id = order_id
        self.table_number = table_number
        self.items_data = items_data

    def execute(self) -> None:
        if self.order_id in self.restaurant.orders:
            logging.error(f"Order {self.order_id} already exists.")
            return

        if self.table_number not in self.restaurant.tables:
            logging.error(f"Table {self.table_number} does not exist.")
            return

        order = Order(
            id=self.order_id,
            table_number=self.table_number,
        )
        for item_data in self.items_data:
            try:
                item = OrderItem(
                    dish_name=item_data["dish_name"],
                    quantity=item_data["quantity"],
                    price=item_data["price"],
                )
                order.add_item(item)
            except KeyError as e:
                logging.error(f"Missing item data: {e}")
                return
            except ValueError as e:
                logging.error(f"Invalid item data: {e}")
                return

        self.restaurant.add_order(order)
        logging.info(f"Order {self.order_id} added.")


class ModifyOrderCommand(Command):

    def __init__(
        self,
        restaurant: Restaurant,
        order_id: int,
        items_data: list = None,
        preparation_status: str = None,
    ):
        self.restaurant = restaurant
        self.order_id = order_id
        self.items_data = items_data
        self.preparation_status = preparation_status

    def execute(self) -> None:
        order = self.restaurant.orders.get(self.order_id)
        if not order:
            logging.error(f"Order {self.order_id} not found.")
            return

        if self.items_data is not None:
            # Clear existing items and add new ones
            order.items.clear()
            for item_data in self.items_data:
                try:
                    item = OrderItem(
                        dish_name=item_data["dish_name"],
                        quantity=item_data["quantity"],
                        price=item_data["price"],
                    )
                    order.add_item(item)
                except KeyError as e:
                    logging.error(f"Missing item data: {e}")
                    return
                except ValueError as e:
                    logging.error(f"Invalid item data: {e}")
                    return

        if self.preparation_status is not None:
            order.preparation_status = self.preparation_status

        logging.info(f"Order {self.order_id} modified.")


class DeleteOrderCommand(Command):

    def __init__(self, restaurant: Restaurant, order_id: int):
        self.restaurant = restaurant
        self.order_id = order_id

    def execute(self) -> None:
        if self.order_id in self.restaurant.orders:
            del self.restaurant.orders[self.order_id]
            logging.info(f"Order {self.order_id} deleted.")
        else:
            logging.error(f"Order {self.order_id} not found.")


class ListOrdersCommand(Command):

    def __init__(self, restaurant: Restaurant):
        self.restaurant = restaurant

    def execute(self) -> None:
        orders = self.restaurant.orders.values()
        if orders:
            for order in orders:
                print(order)
        else:
            logging.info("No orders found.")
