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
        self.geometry("420x350")
        self.configure(padx=10, pady=10)

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        """Create and organize widgets in the dialog"""
        # Order details
        self.create_order_details_section()

        # Payment method selection
        self.create_payment_method_section()

        # Amount paid
        self.create_amount_paid_section()

        # Buttons
        self.create_button_section()

    def create_order_details_section(self):
        """Create the section displaying order details"""
        details_frame = ctk.CTkFrame(self, fg_color="transparent")
        details_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            details_frame,
            text=f"Order #{self.order.id}",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", pady=5)

        ctk.CTkLabel(
            details_frame,
            text=f"Total Amount: ${self.order.total_amount:.2f}",
            font=ctk.CTkFont(size=14),
        ).pack(anchor="w", pady=5)

    def create_payment_method_section(self):
        """Create the section for selecting a payment method"""
        method_frame = ctk.CTkFrame(self, fg_color="transparent")
        method_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            method_frame, text="Payment Method:", font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=5)

        self.payment_method = ctk.StringVar(value=PaymentMethod.CASH.value)
        ctk.CTkOptionMenu(
            method_frame,
            values=[method.value for method in PaymentMethod],
            variable=self.payment_method,
            width=250,
        ).pack(anchor="w", pady=5)

    def create_amount_paid_section(self):
        """Create the section for entering the amount paid"""
        amount_frame = ctk.CTkFrame(self, fg_color="transparent")
        amount_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(amount_frame, text="Amount Paid:", font=ctk.CTkFont(size=14)).pack(
            anchor="w", pady=5
        )
        self.amount_var = ctk.StringVar(value=str(self.order.total_amount))
        ctk.CTkEntry(amount_frame, textvariable=self.amount_var, width=250).pack(
            anchor="w", pady=5
        )

    def create_button_section(self):
        """Create the section for dialog buttons"""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=20)

        ctk.CTkButton(button_frame, text="Cancel", command=self.cancel, width=120).pack(
            side="right", padx=10
        )

        ctk.CTkButton(
            button_frame, text="Process", command=self.process, width=120
        ).pack(side="right")

    def process(self):
        """Handle payment processing"""
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
        """Handle dialog cancellation"""
        self.destroy()

    def center_window(self):
        """Center the dialog window on the screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _show_error(self, title: str, message: str):
        """Show an error dialog with the given title and message"""
        dialog = CTkMessageDialog(self, title, message)
        dialog.wait_window()
