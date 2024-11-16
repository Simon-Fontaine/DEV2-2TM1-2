import sys
import logging
import customtkinter as ctk
from src.utils.logger import setup_logging
from src.utils.database import initialize_database
from src.gui.main_window import MainWindow


def main():
    try:
        setup_logging()
        initialize_database()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        app = MainWindow()
        app.mainloop()

    except Exception as e:
        logging.error(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
