import logging
import customtkinter as ctk

from ...models.table import TableStatus, Table
from ...utils.colors import get_status_color

logger = logging.getLogger(__name__)


class TableCard(ctk.CTkFrame):
    def __init__(self, master, table: Table, on_status_change=None, on_delete=None):
        super().__init__(master, fg_color="transparent")
        self.table = table
        self.on_status_change = on_status_change
        self.on_delete = on_delete
        self.initialize_ui()
        self.update_status_display()

    def initialize_ui(self):
        # Configure grid columns
        self.grid_columnconfigure(1, weight=1)  # Make middle space expandable

        # Info section (left side)
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        table_info = ctk.CTkLabel(
            info_frame,
            text=f"Table {self.table.number}",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        table_info.pack(side="left")

        # Small bullet separator
        separator = ctk.CTkLabel(info_frame, text=" • ", font=ctk.CTkFont(size=14))
        separator.pack(side="left")

        capacity_info = ctk.CTkLabel(
            info_frame,
            text=f"Capacity: {self.table.capacity}",
            font=ctk.CTkFont(size=14),
        )
        capacity_info.pack(side="left")

        # Small bullet separator
        separator2 = ctk.CTkLabel(info_frame, text=" • ", font=ctk.CTkFont(size=14))
        separator2.pack(side="left")

        location_info = ctk.CTkLabel(
            info_frame, text=self.table.location, font=ctk.CTkFont(size=14)
        )
        location_info.pack(side="left")

        # Controls section (right side)
        controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        controls_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")

        # Status dropdown
        self.status_var = ctk.StringVar(value=self.table.status.value)
        self.status_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=[status.value for status in TableStatus],
            variable=self.status_var,
            command=self._on_status_change,
            width=140,  # Slightly wider for better text display
            height=32,  # Standard height
        )
        self.status_menu.pack(side="left", padx=(0, 10))

        # Delete button
        delete_button = ctk.CTkButton(
            controls_frame,
            text="×",
            width=32,
            height=32,
            command=self._on_delete,
            fg_color="red",
            hover_color="darkred",
            corner_radius=8,
        )
        delete_button.pack(side="left")

    def update_status_display(self):
        self.status_var.set(self.table.status.value)
        self.status_menu.configure(fg_color=get_status_color(self.table.status))

    def _on_status_change(self, new_status: str):
        if self.on_status_change:
            self.on_status_change(self.table, TableStatus(new_status))
            # Update color immediately after status change
            self.table.status = TableStatus(new_status)
            self.update_status_display()

    def _on_delete(self):
        if self.on_delete:
            self.on_delete(self.table)
