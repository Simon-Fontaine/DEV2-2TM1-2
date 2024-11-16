import logging
import customtkinter as ctk

from .message_dialog import CTkMessageDialog

logger = logging.getLogger(__name__)


class TableDialog(ctk.CTkToplevel):
    """Dialog for adding/editing tables"""

    def __init__(self, parent, title="Add Table"):
        super().__init__(parent)

        self.title(title)
        self.geometry("400x300")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Initialize result
        self.result = None

        # Create form fields
        self.create_widgets()

        # Center the dialog
        self.center_window()

    def create_widgets(self):
        # Table number
        number_frame = ctk.CTkFrame(self, fg_color="transparent")
        number_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(number_frame, text="Table Number:").pack(side="left")
        self.number_var = ctk.StringVar()
        self.number_entry = ctk.CTkEntry(number_frame, textvariable=self.number_var)
        self.number_entry.pack(side="right", expand=True, fill="x", padx=(10, 0))

        # Capacity
        capacity_frame = ctk.CTkFrame(self, fg_color="transparent")
        capacity_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(capacity_frame, text="Capacity:").pack(side="left")
        self.capacity_var = ctk.StringVar()
        self.capacity_entry = ctk.CTkEntry(
            capacity_frame, textvariable=self.capacity_var
        )
        self.capacity_entry.pack(side="right", expand=True, fill="x", padx=(10, 0))

        # Location
        location_frame = ctk.CTkFrame(self, fg_color="transparent")
        location_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(location_frame, text="Location:").pack(side="left")
        self.location_var = ctk.StringVar()
        self.location_entry = ctk.CTkEntry(
            location_frame, textvariable=self.location_var
        )
        self.location_entry.pack(side="right", expand=True, fill="x", padx=(10, 0))

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(button_frame, text="Cancel", command=self.cancel, width=100).pack(
            side="right", padx=5
        )

        ctk.CTkButton(button_frame, text="Save", command=self.save, width=100).pack(
            side="right", padx=5
        )

    def save(self):
        try:
            # Validate inputs
            number = int(self.number_var.get())
            capacity = int(self.capacity_var.get())
            location = self.location_var.get().strip()

            if number <= 0:
                raise ValueError("Table number must be positive")
            if capacity <= 0:
                raise ValueError("Capacity must be positive")
            if not location:
                raise ValueError("Location is required")

            self.result = {"number": number, "capacity": capacity, "location": location}
            self.destroy()

        except ValueError as e:
            self._show_error("Validation Error", str(e))

    def cancel(self):
        self.destroy()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _show_error(self, title: str, message: str):
        dialog = CTkMessageDialog(self, title, message)
        dialog.wait_window()
