import logging
from datetime import datetime, timedelta
import customtkinter as ctk
from typing import Optional, List
from tkcalendar import DateEntry

from ...models.reservation import Reservation, ReservationStatus, ReservationPriority
from ...models.table import Table
from ...services.customer_service import CustomerService
from ...services.table_service import TableService
from .message_dialog import CTkMessageDialog

logger = logging.getLogger(__name__)


class ReservationDialog(ctk.CTkToplevel):
    """Dialog for creating/editing reservations"""

    def __init__(
        self,
        parent,
        customer_service: CustomerService,
        table_service: TableService,
        title: str = "New Reservation",
        reservation: Optional[Reservation] = None,
    ):
        super().__init__(parent)
        self.customer_service = customer_service
        self.table_service = table_service
        self.reservation = reservation
        self.result = None
        self.selected_customer = None
        self.selected_tables: List[Table] = []

        self.title(title)
        self.geometry("800x600")
        self.configure(padx=20, pady=20)

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if reservation:
            self.fill_fields(reservation)

        self.center_window()

    def create_widgets(self):
        """Create dialog widgets with scrollable content"""
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Create scrollable content frame
        self.content = ctk.CTkScrollableFrame(self.main_container)
        self.content.pack(fill="both", expand=True, padx=5, pady=5)
        self.content.grid_columnconfigure(1, weight=1)

        # Add all sections to scrollable content
        current_row = 0

        # Customer section with reduced padding
        self._create_customer_section(current_row)
        current_row += 1

        # Date and time (combined in one row)
        self._create_datetime_section(current_row)
        current_row += 1

        # Party details with shorter height
        self._create_party_details_section(current_row)
        current_row += 1

        # Table selection with dynamic height
        self._create_table_section(current_row)
        current_row += 1

        # Additional details with reduced textbox heights
        self._create_additional_details_section(current_row)
        current_row += 1

        # Buttons at the bottom, outside scrollable area
        self._create_button_section()

    def _create_customer_section(self, row):
        """Create compact customer selection section"""
        frame = ctk.CTkFrame(self.content)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        frame.grid_columnconfigure(1, weight=1)

        # Header and search in one row
        ctk.CTkLabel(frame, text="Customer:", font=ctk.CTkFont(weight="bold")).pack(
            side="left", padx=5
        )

        self.customer_search = ctk.StringVar()
        self.customer_search.trace_add("write", self._on_customer_search)

        self.customer_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Search customers...",
            textvariable=self.customer_search,
        )
        self.customer_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Results frame with reduced height
        self.customer_results = ctk.CTkScrollableFrame(frame, height=80)
        self.customer_results.pack(fill="x", pady=(5, 0))

    def _create_datetime_section(self, row):
        """Create compact date/time selection"""
        frame = ctk.CTkFrame(self.content)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)

        # Date selection
        date_frame = ctk.CTkFrame(frame, fg_color="transparent")
        date_frame.pack(side="left", padx=10)

        ctk.CTkLabel(date_frame, text="Date:", font=ctk.CTkFont(weight="bold")).pack(
            side="left"
        )
        self.date_entry = DateEntry(
            date_frame,
            width=12,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            mindate=datetime.now(),
        )
        self.date_entry.pack(side="left", padx=5)

        # Time selection
        time_frame = ctk.CTkFrame(frame, fg_color="transparent")
        time_frame.pack(side="left", padx=10)

        ctk.CTkLabel(time_frame, text="Time:", font=ctk.CTkFont(weight="bold")).pack(
            side="left"
        )

        self.hour_var = ctk.StringVar(value="12")
        self.hour_menu = ctk.CTkOptionMenu(
            time_frame,
            values=[str(h).zfill(2) for h in range(24)],
            variable=self.hour_var,
            width=70,
            command=self._on_time_change,
        )
        self.hour_menu.pack(side="left", padx=5)

        ctk.CTkLabel(time_frame, text=":").pack(side="left")

        self.minute_var = ctk.StringVar(value="00")
        self.minute_menu = ctk.CTkOptionMenu(
            time_frame,
            values=["00", "15", "30", "45"],
            variable=self.minute_var,
            width=70,
            command=self._on_time_change,
        )
        self.minute_menu.pack(side="left", padx=5)

    def _create_party_details_section(self):
        """Create party size and duration section"""
        details_frame = ctk.CTkFrame(self)
        details_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        details_frame.grid_columnconfigure(1, weight=1)

        # Party size
        ctk.CTkLabel(
            details_frame, text="Party Size:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=5, pady=5)

        self.party_size_var = ctk.StringVar(value="2")
        self.party_size_entry = ctk.CTkEntry(
            details_frame, textvariable=self.party_size_var, width=100
        )
        self.party_size_entry.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.party_size_var.trace_add("write", self._on_party_size_change)

        # Duration
        ctk.CTkLabel(
            details_frame, text="Duration:", font=ctk.CTkFont(weight="bold")
        ).grid(row=1, column=0, padx=5, pady=5)

        duration_frame = ctk.CTkFrame(details_frame)
        duration_frame.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        self.duration_var = ctk.StringVar(value="120")
        self.duration_entry = ctk.CTkEntry(
            duration_frame, textvariable=self.duration_var, width=100
        )
        self.duration_entry.pack(side="left")

        ctk.CTkLabel(duration_frame, text="minutes").pack(side="left", padx=(5, 0))

        self.duration_var.trace_add("write", self._on_duration_change)

    def _create_table_section(self):
        """Create table selection section"""
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        table_frame.grid_columnconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

        ctk.CTkLabel(
            header_frame, text="Select Tables:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=5)

        self.check_tables_button = ctk.CTkButton(
            header_frame,
            text="Check Available Tables",
            command=self._check_available_tables,
            width=150,
        )
        self.check_tables_button.pack(side="right", padx=5)

        # Available tables list
        self.tables_frame = ctk.CTkScrollableFrame(table_frame, height=150)
        self.tables_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

    def _create_party_details_section(self, row):
        """Create compact party details section"""
        frame = ctk.CTkFrame(self.content)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)

        # Party size
        size_frame = ctk.CTkFrame(frame, fg_color="transparent")
        size_frame.pack(side="left", padx=10)

        ctk.CTkLabel(
            size_frame, text="Party Size:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left")
        self.party_size_var = ctk.StringVar(value="2")
        self.party_size_entry = ctk.CTkEntry(
            size_frame, textvariable=self.party_size_var, width=70
        )
        self.party_size_entry.pack(side="left", padx=5)

        # Duration
        duration_frame = ctk.CTkFrame(frame, fg_color="transparent")
        duration_frame.pack(side="left", padx=10)

        ctk.CTkLabel(
            duration_frame, text="Duration:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left")
        self.duration_var = ctk.StringVar(value="120")
        self.duration_entry = ctk.CTkEntry(
            duration_frame, textvariable=self.duration_var, width=70
        )
        self.duration_entry.pack(side="left", padx=5)
        ctk.CTkLabel(duration_frame, text="min").pack(side="left")

    def _create_table_section(self, row):
        """Create compact table selection section"""
        frame = ctk.CTkFrame(self.content)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(frame, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(header, text="Tables:", font=ctk.CTkFont(weight="bold")).pack(
            side="left"
        )
        ctk.CTkButton(
            header,
            text="Check Available",
            command=self._check_available_tables,
            width=120,
        ).pack(side="right")

        self.tables_frame = ctk.CTkScrollableFrame(frame, height=120)
        self.tables_frame.pack(fill="x", pady=2)

    def _create_additional_details_section(self, row):
        """Create compact additional details section"""
        frame = ctk.CTkFrame(self.content)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)

        # Priority in one line
        priority_frame = ctk.CTkFrame(frame, fg_color="transparent")
        priority_frame.pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(
            priority_frame, text="Priority:", font=ctk.CTkFont(weight="bold")
        ).pack(side="left")

        self.priority_var = ctk.StringVar(value=ReservationPriority.MEDIUM.value)
        ctk.CTkOptionMenu(
            priority_frame,
            values=[p.value for p in ReservationPriority],
            variable=self.priority_var,
            width=120,
        ).pack(side="left", padx=5)

        # Combine notes and requests in two columns
        details_frame = ctk.CTkFrame(frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=5, pady=2)
        details_frame.grid_columnconfigure(1, weight=1)
        details_frame.grid_columnconfigure(3, weight=1)

        # Notes
        ctk.CTkLabel(
            details_frame, text="Notes:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, padx=5)

        self.notes_text = ctk.CTkTextbox(details_frame, height=50, width=200)
        self.notes_text.grid(row=0, column=1, padx=5, sticky="ew")

        # Special Requests
        ctk.CTkLabel(
            details_frame, text="Requests:", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=2, padx=5)

        self.requests_text = ctk.CTkTextbox(details_frame, height=50, width=200)
        self.requests_text.grid(row=0, column=3, padx=5, sticky="ew")

    def _create_button_section(self):
        """Create button section at bottom of window"""
        button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            width=100,
            fg_color="gray",
            hover_color="darkgray",
        ).pack(side="right", padx=5)

        ctk.CTkButton(button_frame, text="Save", command=self.save, width=100).pack(
            side="right", padx=5
        )

    def _on_customer_search(self, *args):
        """Handle customer search"""
        search_text = self.customer_search.get().strip()

        # Clear previous results
        for widget in self.customer_results.winfo_children():
            widget.destroy()

        if search_text:
            customers = self.customer_service.search_customers(search_text)

            for customer in customers:
                customer_frame = ctk.CTkFrame(
                    self.customer_results, fg_color="transparent"
                )
                customer_frame.pack(fill="x", padx=2, pady=1)

                ctk.CTkLabel(
                    customer_frame,
                    text=f"{customer.name} ({customer.phone})",
                    font=ctk.CTkFont(size=12),
                ).pack(side="left", padx=5)

                ctk.CTkButton(
                    customer_frame,
                    text="Select",
                    width=60,
                    height=24,
                    command=lambda c=customer: self._select_customer(c),
                ).pack(side="right", padx=5)

    def _check_available_tables(self):
        """Check and display available tables"""
        try:
            # Validate inputs
            if not self._check_datetime_validity():
                return

            if not self.party_size_var.get().isdigit():
                self._show_error("Invalid Input", "Please enter a valid party size")
                return

            if not self.duration_var.get().isdigit():
                self._show_error("Invalid Input", "Please enter a valid duration")
                return

            party_size = int(self.party_size_var.get())
            duration = int(self.duration_var.get())
            reservation_time = self._get_selected_datetime()

            # Get available tables using the renamed method
            available_tables = self.table_service.get_available_for_reservation(
                reservation_time=reservation_time,
                duration=duration,
                party_size=party_size,
            )

            # Display available tables
            self._display_available_tables(available_tables)

        except Exception as e:
            logger.error(f"Error checking available tables: {e}")
            self._show_error("Error", str(e))

    def _select_customer(self, customer):
        """Handle customer selection"""
        self.selected_customer = customer
        self.customer_search.set(f"{customer.name} ({customer.phone})")

        # Clear customer list
        for widget in self.customer_results.winfo_children():
            widget.destroy()

    def _on_time_change(self, *args):
        """Handle time selection change"""
        self._check_datetime_validity()
        self.selected_tables.clear()
        self._update_tables_display()

    def _on_party_size_change(self, *args):
        """Handle party size change"""
        self.selected_tables.clear()
        self._update_tables_display()

    def _on_duration_change(self, *args):
        """Handle duration change"""
        self.selected_tables.clear()
        self._update_tables_display()

    def _check_datetime_validity(self):
        """Check if selected date/time is valid"""
        try:
            selected_dt = self._get_selected_datetime()
            if selected_dt < datetime.now():
                self._show_error("Invalid Time", "Selected time must be in the future")
                return False
            return True
        except ValueError:
            return False

    def _get_selected_datetime(self) -> datetime:
        """Get selected date and time as datetime object"""
        selected_date = self.date_entry.get_date()
        hour = int(self.hour_var.get())
        minute = int(self.minute_var.get())
        return datetime(
            selected_date.year, selected_date.month, selected_date.day, hour, minute
        )

    def _display_available_tables(self, available_tables: List[Table]):
        """Display available tables in the tables frame"""
        # Clear previous display
        for widget in self.tables_frame.winfo_children():
            widget.destroy()

        if not available_tables:
            ctk.CTkLabel(
                self.tables_frame,
                text="No tables available for selected criteria",
                text_color="red",
            ).pack(pady=10)
            return

        # Create checkboxes for each table
        for table in available_tables:
            table_frame = ctk.CTkFrame(self.tables_frame, fg_color="transparent")
            table_frame.pack(fill="x", pady=2)

            var = ctk.BooleanVar(value=table in self.selected_tables)
            checkbox = ctk.CTkCheckBox(
                table_frame,
                text=f"Table {table.number} (Capacity: {table.capacity})",
                variable=var,
                command=lambda t=table, v=var: self._on_table_selection(t, v),
            )
            checkbox.pack(side="left", padx=5)

    def _on_table_selection(self, table: Table, var: ctk.BooleanVar):
        """Handle table selection/deselection"""
        if var.get() and table not in self.selected_tables:
            self.selected_tables.append(table)
        elif not var.get() and table in self.selected_tables:
            self.selected_tables.remove(table)

    def _update_tables_display(self):
        """Update tables display when selection criteria change"""
        # Clear current display
        for widget in self.tables_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.tables_frame,
            text="Click 'Check Available Tables' to see options",
            text_color="gray",
        ).pack(pady=10)

    def fill_fields(self, reservation: Reservation):
        """Fill dialog fields with reservation data"""
        # Customer
        self.selected_customer = reservation.customer
        self.customer_search.set(
            f"{reservation.customer.name} ({reservation.customer.phone})"
        )

        # Date and time
        self.date_entry.set_date(reservation.reservation_datetime.date())
        self.hour_var.set(str(reservation.reservation_datetime.hour).zfill(2))
        self.minute_var.set(str(reservation.reservation_datetime.minute).zfill(2))

        # Party size and duration
        self.party_size_var.set(str(reservation.party_size))
        self.duration_var.set(str(reservation.duration))

        # Tables
        self.selected_tables = reservation.tables
        self._check_available_tables()  # This will refresh the display

        # Priority and notes
        self.priority_var.set(reservation.priority.value)
        if reservation.notes:
            self.notes_text.delete("0.0", "end")
            self.notes_text.insert("0.0", reservation.notes)
        if reservation.special_requests:
            self.requests_text.delete("0.0", "end")
            self.requests_text.insert("0.0", reservation.special_requests)

    def validate(self) -> bool:
        """Validate form inputs"""
        if not self.selected_customer:
            self._show_error("Validation Error", "Please select a customer")
            return False

        try:
            party_size = int(self.party_size_var.get())
            if party_size <= 0:
                raise ValueError()
        except ValueError:
            self._show_error("Validation Error", "Please enter a valid party size")
            return False

        try:
            duration = int(self.duration_var.get())
            if duration < 30 or duration > 480:
                raise ValueError()
        except ValueError:
            self._show_error(
                "Validation Error", "Duration must be between 30 and 480 minutes"
            )
            return False

        if not self._check_datetime_validity():
            return False

        if not self.selected_tables:
            self._show_error("Validation Error", "Please select at least one table")
            return False

        # Validate total table capacity
        total_capacity = sum(table.capacity for table in self.selected_tables)
        if total_capacity < party_size:
            self._show_error(
                "Validation Error", "Selected tables cannot accommodate the party size"
            )
            return False

        return True

    def save(self):
        """Save the reservation data"""
        try:
            if not self.validate():
                return

            # Prepare the result
            self.result = {
                "customer_id": self.selected_customer.id,
                "reservation_datetime": self._get_selected_datetime(),
                "party_size": int(self.party_size_var.get()),
                "duration": int(self.duration_var.get()),
                "table_ids": [table.id for table in self.selected_tables],
                "priority": ReservationPriority(self.priority_var.get()),
                "notes": self.notes_text.get("0.0", "end").strip() or None,
                "special_requests": self.requests_text.get("0.0", "end").strip()
                or None,
            }

            self.destroy()

        except Exception as e:
            logger.error(f"Error saving reservation: {e}")
            self._show_error("Error", str(e))

    def cancel(self):
        """Cancel the dialog"""
        self.destroy()

    def center_window(self):
        """Center the dialog on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _show_error(self, title: str, message: str):
        """Show error dialog"""
        dialog = CTkMessageDialog(self, title, message)
        dialog.wait_window()
