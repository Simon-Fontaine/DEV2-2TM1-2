import sys
import logging
import customtkinter as ctk
from sqlalchemy.orm import sessionmaker, scoped_session

from src.models.base_model import engine
from src.utils.logger import setup_logging
from src.gui.main_window import MainWindow
from src.utils.database import initialize_database
from src.services.table_service import TableService
from src.services.customer_service import CustomerService
from src.services.menu_item_service import MenuItemService
from src.services.order_service import OrderService
from src.services.reservation_service import ReservationService
from src.models.table import Table
from src.models.customer import Customer
from src.models.menu_item import MenuItem
from src.models.order import Order
from src.models.reservation import Reservation


def main():
    try:
        setup_logging()
        initialize_database()

        Session = sessionmaker(bind=engine, expire_on_commit=False)
        session_factory = scoped_session(Session)

        table_service = TableService(Table, session_factory)
        customer_service = CustomerService(Customer, session_factory)
        menu_service = MenuItemService(MenuItem, session_factory)
        order_service = OrderService(Order, session_factory)
        reservation_service = ReservationService(Reservation, session_factory)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        app = MainWindow(
            table_service=table_service,
            customer_service=customer_service,
            menu_service=menu_service,
            order_service=order_service,
            reservation_service=reservation_service,
        )
        app.mainloop()

    except Exception as e:
        logging.error(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
