import logging
import customtkinter as ctk
from ...models.order import Order, PaymentMethod
from .message_dialog import CTkMessageDialog

logger = logging.getLogger(__name__)


class PaymentDialog(ctk.CTkToplevel):
    """Dialog for processing payments"""

    def __init__(self, parent, order: Order):
        super().__init__(parent)
        self.order = order
        self.result = None

        self.title("Process Payment")
        self.geometry("400x300")

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        # Order details
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            details_frame,
            text=f"Order #{self.order.id}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w")

        ctk.CTkLabel(
            details_frame,
            text=f"Total Amount: ${self.order.total_amount:.2f}",
            font=ctk.CTkFont(size=14),
        ).pack(anchor="w", pady=5)

        # Payment method selection
        method_frame = ctk.CTkFrame(self, fg_color="transparent")
        method_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(method_frame, text="Payment Method:").pack(anchor="w")

        self.payment_method = ctk.StringVar(value=PaymentMethod.CASH.value)
        method_menu = ctk.CTkOptionMenu(
            method_frame,
            values=[method.value for method in PaymentMethod],
            variable=self.payment_method,
            width=200,
        )
        method_menu.pack(anchor="w", pady=5)

        # Amount paid
        amount_frame = ctk.CTkFrame(self, fg_color="transparent")
        amount_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(amount_frame, text="Amount Paid:").pack(anchor="w")
        self.amount_var = ctk.StringVar(value=str(self.order.total_amount))
        amount_entry = ctk.CTkEntry(amount_frame, textvariable=self.amount_var)
        amount_entry.pack(anchor="w", pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(button_frame, text="Cancel", command=self.cancel, width=100).pack(
            side="right", padx=5
        )

        ctk.CTkButton(
            button_frame, text="Process", command=self.process, width=100
        ).pack(side="right", padx=5)

    def process(self):
        try:
            amount_paid = float(self.amount_var.get())
            if amount_paid < self.order.total_amount:
                self._show_error(
                    "Invalid Amount", "Payment amount must cover the total"
                )
                return

            self.result = {
                "payment_method": PaymentMethod(self.payment_method.get()),
                "amount_paid": amount_paid,
            }
            self.destroy()
        except ValueError:
            self._show_error("Invalid Input", "Please enter a valid amount")

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
