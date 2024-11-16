import logging
from typing import Dict, Optional, List, Tuple, Type
import customtkinter as ctk
from ..controllers.table_controller import TableController
from .views import TablesView, OrdersView, MenuView, CustomersView, ReservationsView

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialize controllers
        self.table_controller = TableController()

        self.title("Restaurant Manager")
        self.geometry("1200x800")

        # Define navigation items with factory functions for views that need controllers
        self.navigation_items: List[Tuple[str, str, Type[ctk.CTkFrame], dict]] = [
            ("tables", "Tables", TablesView, {"controller": self.table_controller}),
            ("orders", "Orders", OrdersView, {}),
            ("menu", "Menu", MenuView, {}),
            ("customers", "Customers", CustomersView, {}),
            ("reservations", "Reservations", ReservationsView, {}),
        ]

        self.sidebar_buttons: Dict[str, ctk.CTkButton] = {}
        self.content_frames: Dict[str, ctk.CTkFrame] = {}
        self.active_button: Optional[str] = None

        self.initialize_ui()
        self.create_content_frames()
        self.setup_navigation()

    def initialize_ui(self):
        """Initialize the main window UI with sidebar and main content area"""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()

        # Create main content area
        self.main_content = ctk.CTkFrame(self, corner_radius=0)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(0, weight=1)

    def create_sidebar(self):
        """Create and configure the sidebar with evenly spaced buttons"""
        # Create sidebar frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)
        self.sidebar_frame.grid_columnconfigure(0, weight=1)

        # Create equal rows for each element (logo + buttons + spacing)
        total_rows = len(self.navigation_items) + 2
        for i in range(total_rows):
            self.sidebar_frame.grid_rowconfigure(i, weight=1)

        # App title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Restaurant\nManager",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Create buttons from navigation items
        for idx, (btn_id, btn_text, _, _) in enumerate(self.navigation_items, start=1):
            button = ctk.CTkButton(
                self.sidebar_frame, text=btn_text, width=160, height=40
            )
            button.grid(row=idx, column=0, padx=20, sticky="n")
            self.sidebar_buttons[btn_id] = button

    def create_content_frames(self):
        """Create content frames for each section"""
        for view_id, _, view_class, view_kwargs in self.navigation_items:
            frame = view_class(self.main_content, **view_kwargs)
            self.content_frames[view_id] = frame

    def show_content(self, content_id: str):
        """Show the selected content and update button states"""
        if self.active_button:
            self.sidebar_buttons[self.active_button].configure(state="normal")

        self.sidebar_buttons[content_id].configure(state="disabled")
        self.active_button = content_id

        for frame in self.content_frames.values():
            frame.grid_forget()

        # Show selected frame
        self.content_frames[content_id].grid(
            row=0, column=0, sticky="nsew", padx=10, pady=10
        )

    def setup_navigation(self):
        """Setup navigation commands for all buttons"""
        for btn_id in self.sidebar_buttons:
            self.sidebar_buttons[btn_id].configure(
                command=lambda id=btn_id: self.show_content(id)
            )

        # Show first navigation item by default
        if self.navigation_items:
            self.show_content(self.navigation_items[0][0])
