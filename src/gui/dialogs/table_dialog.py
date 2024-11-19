import logging
import customtkinter as ctk
from .message_dialog import CTkMessageDialog
from ...models.table import TableStatus

logger = logging.getLogger(__name__)


class TableDialog(ctk.CTkToplevel):
    def __init__(self, parent, title="Add Table", table=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("300x250")

        self.transient(parent)
        self.grab_set()

        self.result = None
        self.table = table

        self._create_widgets()
        if table:
            self._fill_fields(table)
        self._center_window()

    def _create_widgets(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # Table number
        number_frame = ctk.CTkFrame(container, fg_color="transparent", height=40)
        number_frame.pack(fill="x", pady=5)
        number_frame.pack_propagate(False)

        ctk.CTkLabel(number_frame, text="Table Number:", width=100).pack(side="left")
        self.number_var = ctk.StringVar()
        self.number_entry = ctk.CTkEntry(
            number_frame, textvariable=self.number_var, width=150
        )
        self.number_entry.pack(side="right")

        # Capacity
        capacity_frame = ctk.CTkFrame(container, fg_color="transparent", height=40)
        capacity_frame.pack(fill="x", pady=5)
        capacity_frame.pack_propagate(False)

        ctk.CTkLabel(capacity_frame, text="Capacity:", width=100).pack(side="left")
        self.capacity_var = ctk.StringVar()
        self.capacity_entry = ctk.CTkEntry(
            capacity_frame, textvariable=self.capacity_var, width=150
        )
        self.capacity_entry.pack(side="right")

        # Status (for editing only)
        if self.table:
            status_frame = ctk.CTkFrame(container, fg_color="transparent", height=40)
            status_frame.pack(fill="x", pady=5)
            status_frame.pack_propagate(False)

            ctk.CTkLabel(status_frame, text="Status:", width=100).pack(side="left")
            self.status_var = ctk.StringVar()
            self.status_menu = ctk.CTkOptionMenu(
                status_frame,
                values=[status.value for status in TableStatus],
                variable=self.status_var,
                width=150,
            )
            self.status_menu.pack(side="right")

        # Buttons
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            width=80,
            fg_color="grey",
            hover_color="darkgrey",
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(button_frame, text="Save", command=self.save, width=80).pack(
            side="right"
        )

    def _fill_fields(self, table):
        self.number_var.set(str(table.number))
        self.capacity_var.set(str(table.capacity))
        if hasattr(self, "status_var"):
            self.status_var.set(table.status.value)

    def save(self):
        try:
            if not self.number_var.get().isdigit():
                raise ValueError("Table number must be an integer")
            if not self.capacity_var.get().isdigit():
                raise ValueError("Capacity must be an integer")

            number = int(self.number_var.get())
            capacity = int(self.capacity_var.get())

            if number <= 0:
                raise ValueError("Table number must be positive")
            if capacity <= 0:
                raise ValueError("Capacity must be positive")

            self.result = {
                "number": number,
                "capacity": capacity,
            }

            if self.table and hasattr(self, "status_var"):
                self.result["status"] = TableStatus(self.status_var.get())
            elif not self.table:
                self.result["status"] = TableStatus.AVAILABLE

            self.destroy()

        except ValueError as e:
            self._show_error("Validation Error", str(e))

    def cancel(self):
        self.destroy()

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _show_error(self, title: str, message: str):
        dialog = CTkMessageDialog(self, title, message)
        dialog.wait_window()
