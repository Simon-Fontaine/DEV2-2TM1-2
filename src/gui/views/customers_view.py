import logging
from typing import Dict, Optional
import customtkinter as ctk
from datetime import datetime

from .base_view import BaseView
from ..dialogs.customer_dialog import CustomerDialog
from ...models.customer import Customer
from ...services.customer_service import CustomerService

logger = logging.getLogger(__name__)


class CustomersView(BaseView[Customer]):
    def __init__(self, master: any, service: CustomerService):
        self.customers: Dict[int, Customer] = {}
        super().__init__(master, service)
        self.refresh()

    def initialize_ui(self):
        """Initialize the UI components"""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._create_header()
        self._create_search_bar()
        self._create_customers_list()

    def _create_header(self):
        """Create header with title and add button"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        header.grid_columnconfigure(2, weight=1)

        # Title
        ctk.CTkLabel(
            header,
            text="Customers Management",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=10)

        # Add Customer button
        ctk.CTkButton(
            header, text="Add Customer", width=120, command=self._handle_add_customer
        ).grid(row=0, column=1, padx=10, pady=10)

        # Refresh button
        ctk.CTkButton(header, text="Refresh", width=100, command=self.refresh).grid(
            row=0, column=2, padx=10, pady=10
        )

    def _create_search_bar(self):
        """Create search bar"""
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search customers by name, phone, or email...",
            textvariable=self.search_var,
        )
        search_entry.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

    def _create_customers_list(self):
        """Create scrollable customers list"""
        # Container frame
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Scrollable frame for customers
        self.customers_frame = ctk.CTkScrollableFrame(container)
        self.customers_frame.grid(row=0, column=0, sticky="nsew")
        self.customers_frame.grid_columnconfigure(0, weight=1)

    def _create_customer_card(self, customer: Customer, row: int):
        """Create a card for displaying customer information"""
        card = ctk.CTkFrame(self.customers_frame)
        card.grid(row=row, column=0, padx=5, pady=5, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # Customer info section
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # ID and Name
        id_name = ctk.CTkLabel(
            info_frame,
            text=f"#{customer.id} - {customer.name}",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        id_name.pack(side="left", padx=(0, 10))

        # Separator
        ctk.CTkLabel(info_frame, text="|").pack(side="left", padx=5)

        # Phone
        ctk.CTkLabel(info_frame, text=f"Phone: {customer.phone}").pack(
            side="left", padx=5
        )

        # Email (if available)
        if customer.email:
            ctk.CTkLabel(info_frame, text="|").pack(side="left", padx=5)
            ctk.CTkLabel(info_frame, text=f"Email: {customer.email}").pack(
                side="left", padx=5
            )

        # Controls section
        controls_frame = ctk.CTkFrame(card, fg_color="transparent")
        controls_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")

        # Edit button
        ctk.CTkButton(
            controls_frame,
            text="Edit",
            width=70,
            command=lambda: self._handle_edit_customer(customer),
        ).pack(side="left", padx=5)

        # Delete button
        ctk.CTkButton(
            controls_frame,
            text="Delete",
            width=70,
            fg_color="red",
            hover_color="darkred",
            command=lambda: self._handle_delete_customer(customer),
        ).pack(side="left", padx=5)

        # Notes section (if available)
        if customer.notes:
            notes_frame = ctk.CTkFrame(card, fg_color="transparent")
            notes_frame.grid(
                row=1, column=0, columnspan=3, padx=10, pady=(0, 5), sticky="ew"
            )
            ctk.CTkLabel(
                notes_frame, text=f"Notes: {customer.notes}", wraplength=600
            ).pack(fill="x")

    def refresh(self, search_query: str = ""):
        """Refresh the customers display"""
        try:
            # Clear existing customer cards
            for widget in self.customers_frame.winfo_children():
                widget.destroy()
            self.customers.clear()

            # Get customers (filtered if search query exists)
            customers = (
                self.service.search_customers(search_query)
                if search_query
                else self.service.get_all()
            )

            # Display customers
            for idx, customer in enumerate(customers):
                self._create_customer_card(customer, idx)
                self.customers[customer.id] = customer

        except Exception as e:
            logger.error(f"Error refreshing customers view: {e}")
            self.show_error("Error", f"Failed to refresh customers: {str(e)}")

    def _on_search(self, *args):
        """Handle search input changes"""
        search_text = self.search_var.get().strip()
        self.refresh(search_text)

    def _handle_add_customer(self):
        """Handle adding a new customer"""
        dialog = CustomerDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            try:
                # Check if customer with same phone already exists
                existing = self.service.get_customer_by_phone(dialog.result["phone"])
                if existing:
                    self.show_error(
                        "Duplicate Customer",
                        f"A customer with phone number {dialog.result['phone']} already exists.",
                    )
                    return

                # Check email uniqueness if provided
                if dialog.result.get("email"):
                    existing = self.service.get_customer_by_email(
                        dialog.result["email"]
                    )
                    if existing:
                        self.show_error(
                            "Duplicate Customer",
                            f"A customer with email {dialog.result['email']} already exists.",
                        )
                        return

                self.service.create(**dialog.result)
                self.refresh()
            except Exception as e:
                logger.error(f"Error creating customer: {e}")
                self.show_error("Error", f"Failed to create customer: {str(e)}")

    def _handle_edit_customer(self, customer: Customer):
        """Handle editing an existing customer"""
        dialog = CustomerDialog(self, title="Edit Customer", customer=customer)
        self.wait_window(dialog)

        if dialog.result:
            try:
                # Check phone uniqueness (excluding current customer)
                existing = self.service.get_customer_by_phone(dialog.result["phone"])
                if existing and existing.id != customer.id:
                    self.show_error(
                        "Duplicate Phone",
                        f"Another customer with phone number {dialog.result['phone']} already exists.",
                    )
                    return

                # Check email uniqueness if provided (excluding current customer)
                if dialog.result.get("email"):
                    existing = self.service.get_customer_by_email(
                        dialog.result["email"]
                    )
                    if existing and existing.id != customer.id:
                        self.show_error(
                            "Duplicate Email",
                            f"Another customer with email {dialog.result['email']} already exists.",
                        )
                        return

                self.service.update(customer.id, **dialog.result)
                self.refresh()
            except Exception as e:
                logger.error(f"Error updating customer: {e}")
                self.show_error("Error", f"Failed to update customer: {str(e)}")

    def _handle_delete_customer(self, customer: Customer):
        """Handle customer deletion"""
        if self.show_confirm(
            "Confirm Deletion",
            f"Are you sure you want to delete customer {customer.name}? "
            "This will also delete all associated reservations and orders.",
        ):
            try:
                self.service.delete(customer.id)
                self.refresh()
            except Exception as e:
                logger.error(f"Error deleting customer: {e}")
                self.show_error("Error", f"Failed to delete customer: {str(e)}")
