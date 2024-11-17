import logging
import customtkinter as ctk
from typing import Optional, Dict

from .message_dialog import CTkMessageDialog

logger = logging.getLogger(__name__)


class CustomerDialog(ctk.CTkToplevel):
    """Dialog for adding/editing customers"""

    def __init__(self, parent, title="Add Customer", customer=None):
        super().__init__(parent)

        self.title(title)
        self.geometry("500x400")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Initialize result
        self.result = None
        self.customer = customer

        # Create form fields
        self.create_widgets()

        # Fill fields if editing
        if customer:
            self.fill_fields(customer)

        # Center the dialog
        self.center_window()

    def create_widgets(self):
        # Main form container
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Name field
        name_frame = self.create_field_frame(form_frame, "Name:")
        self.name_var = ctk.StringVar()
        self.name_entry = ctk.CTkEntry(name_frame, textvariable=self.name_var)
        self.name_entry.pack(side="right", expand=True, fill="x", padx=(10, 0))

        # Phone field
        phone_frame = self.create_field_frame(form_frame, "Phone:")
        self.phone_var = ctk.StringVar()
        self.phone_entry = ctk.CTkEntry(phone_frame, textvariable=self.phone_var)
        self.phone_entry.pack(side="right", expand=True, fill="x", padx=(10, 0))

        # Email field
        email_frame = self.create_field_frame(form_frame, "Email:")
        self.email_var = ctk.StringVar()
        self.email_entry = ctk.CTkEntry(email_frame, textvariable=self.email_var)
        self.email_entry.pack(side="right", expand=True, fill="x", padx=(10, 0))

        # Notes field
        notes_frame = self.create_field_frame(form_frame, "Notes:")
        self.notes_var = ctk.StringVar()
        self.notes_text = ctk.CTkTextbox(notes_frame, height=100)
        self.notes_text.pack(side="right", expand=True, fill="both", padx=(10, 0))

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(button_frame, text="Cancel", command=self.cancel, width=100).pack(
            side="right", padx=5
        )
        ctk.CTkButton(button_frame, text="Save", command=self.save, width=100).pack(
            side="right", padx=5
        )

    def create_field_frame(self, parent, label_text: str) -> ctk.CTkFrame:
        """Create a frame for a form field with label"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text=label_text, width=80).pack(side="left")
        return frame

    def fill_fields(self, customer):
        """Fill the form fields with customer data"""
        self.name_var.set(customer.name)
        self.phone_var.set(customer.phone)
        self.email_var.set(customer.email or "")
        self.notes_text.delete("0.0", "end")
        if customer.notes:
            self.notes_text.insert("0.0", customer.notes)

    def validate_fields(self) -> Optional[Dict]:
        """Validate form fields and return data if valid"""
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        email = self.email_var.get().strip()
        notes = self.notes_text.get("0.0", "end").strip()

        if not name:
            raise ValueError("Name is required")
        if not phone or len(phone) < 10:
            raise ValueError("Valid phone number is required")
        if email and "@" not in email:
            raise ValueError("Invalid email format")

        data = {"name": name, "phone": phone, "notes": notes or None}
        if email:
            data["email"] = email

        return data

    def save(self):
        try:
            data = self.validate_fields()
            if data:
                self.result = data
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
