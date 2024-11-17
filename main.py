import sys
import logging
import customtkinter as ctk
from sqlalchemy.orm import sessionmaker

from src.models.base import engine
from src.utils.logger import setup_logging
from src.gui.main_window import MainWindow
from src.utils.database import initialize_database
from src.services.table_service import TableService


def main():
    try:
        setup_logging()
        initialize_database()

        Session = sessionmaker(bind=engine, expire_on_commit=False)

        table_service = TableService(Session)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        app = MainWindow(table_service=table_service)
        app.mainloop()

    except Exception as e:
        logging.error(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
