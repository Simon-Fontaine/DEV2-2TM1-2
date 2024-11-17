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

        # Track if the component is destroyed
        self.is_destroyed = False

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
        status_values = [status.value for status in TableStatus]
        self.status_var = ctk.StringVar(value=self.table.status.value)

        self.status_menu = ctk.CTkOptionMenu(
            controls_frame,
            values=status_values,
            variable=self.status_var,
            command=self._on_status_change,
            width=140,
            height=32,
            fg_color=get_status_color(self.table.status),
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
        """Update the status display safely"""
        try:
            if not self.is_destroyed and self.winfo_exists():
                current_status = TableStatus(self.status_var.get())
                self.status_menu.configure(fg_color=get_status_color(current_status))
        except Exception as e:
            logger.error(f"Error updating status display: {e}")

    def _on_status_change(self, new_status: str):
        """Handle status change event"""
        try:
            if not self.is_destroyed and self.on_status_change:
                # Convert string status to enum
                status_enum = TableStatus(new_status)
                # Call the callback with the table and new status
                self.on_status_change(self.table, status_enum)
        except Exception as e:
            logger.error(f"Error in status change handler: {e}")

    def _on_delete(self):
        """Handle delete event"""
        try:
            if not self.is_destroyed and self.on_delete:
                self.on_delete(self.table)
        except Exception as e:
            logger.error(f"Error in delete handler: {e}")

    def destroy(self):
        """Override destroy to mark component as destroyed"""
        self.is_destroyed = True
        super().destroy()
