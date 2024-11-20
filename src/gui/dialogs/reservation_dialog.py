import logging
from datetime import datetime, timedelta
import customtkinter as ctk
from typing import Optional, List
from tkcalendar import DateEntry

from ...models.reservation import Reservation, ReservationStatus, ReservationPriority
from ...models.table import Table, TableStatus
from ...services.customer_service import CustomerService
from ...services.table_service import TableService
from .message_dialog import CTkMessageDialog

logger = logging.getLogger(__name__)


class ReservationDialog(ctk.CTkToplevel):
    """Enhanced dialog for creating/editing reservations"""

    TIME_SLOTS = [
        (hour, minute)
        for hour in range(7, 23)  # 7 AM to 10 PM
        for minute in [0, 15, 30, 45]
    ]

    DURATIONS = [
        ("1 hour", 60),
        ("1.5 hours", 90),
        ("2 hours", 120),
        ("2.5 hours", 150),
        ("3 hours", 180),
        ("4 hours", 240),
    ]

    def __init__(
        self,
        parent,
        customer_service: CustomerService,
        table_service: TableService,
        title: str = "New Reservation",
        reservation: Optional[Reservation] = None,
        initial_datetime: Optional[datetime] = None,
    ):
        super().__init__(parent)
        self.customer_service = customer_service
        self.table_service = table_service
        self.reservation = reservation
        self.result = None
        self.selected_customer = None
        self.selected_tables: List[Table] = []
        self.initial_datetime = initial_datetime or datetime.now()

        self.title(title)
        self.geometry("900x700")
        self.configure(padx=20, pady=20)

        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        if reservation:
            self.fill_fields(reservation)
        else:
            self._set_initial_datetime()

        self.center_window()

    def create_widgets(self):
        """Create dialog widgets with improved layout"""
        # Main container with scrolling
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Create scrollable content frame
        self.content = ctk.CTkScrollableFrame(self.main_container)
        self.content.pack(fill="both", expand=True, padx=10, pady=10)
        self.content.grid_columnconfigure(1, weight=1)

        # Customer Section
        self._create_customer_section()

        # DateTime Section
        self._create_datetime_section()

        # Party Details Section
        self._create_party_details_section()

        # Tables Section
        self._create_tables_section()

        # Additional Details Section
        self._create_additional_details_section()

        # Buttons Section
        self._create_button_section()

    def _create_customer_section(self):
        """Create customer selection section"""
        # Section Frame
        section = ctk.CTkFrame(self.content)
        section.pack(fill="x", pady=10)

        # Header
        ctk.CTkLabel(
            section,
            text="Customer Information",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=10, pady=5, anchor="w")

        # Search Frame
        search_frame = ctk.CTkFrame(section, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=5)
        search_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            search_frame,
            text="Search:",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, padx=5)

        self.customer_search = ctk.StringVar()
        self.customer_search.trace_add("write", self._on_customer_search)

        self.customer_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search by name, phone, or email...",
            textvariable=self.customer_search,
        )
        self.customer_entry.grid(row=0, column=1, sticky="ew", padx=5)

        # Results Frame
        self.customer_results = ctk.CTkScrollableFrame(section, height=100)
        self.customer_results.pack(fill="x", padx=10, pady=5)

    def _create_datetime_section(self):
        """Create date and time selection section"""
        section = ctk.CTkFrame(self.content)
        section.pack(fill="x", pady=10)

        ctk.CTkLabel(
            section,
            text="Date and Time",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=10, pady=5, anchor="w")

        # Date and Time Frame
        datetime_frame = ctk.CTkFrame(section, fg_color="transparent")
        datetime_frame.pack(fill="x", padx=10, pady=5)
        datetime_frame.grid_columnconfigure(1, weight=1)
        datetime_frame.grid_columnconfigure(3, weight=1)

        # Date Selection
        ctk.CTkLabel(
            datetime_frame,
            text="Date:",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, padx=5)

        self.date_entry = DateEntry(
            datetime_frame,
            width=12,
            background="#1f1f1f",
            foreground="white",
            borderwidth=2,
            mindate=datetime.now(),
        )
        self.date_entry.grid(row=0, column=1, sticky="w", padx=5)

        # Time Selection
        ctk.CTkLabel(
            datetime_frame,
            text="Time:",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=2, padx=5)

        time_options = [f"{hour:02d}:{minute:02d}" for hour, minute in self.TIME_SLOTS]
        self.time_var = ctk.StringVar()
        self.time_menu = ctk.CTkOptionMenu(
            datetime_frame,
            values=time_options,
            variable=self.time_var,
            width=100,
        )
        self.time_menu.grid(row=0, column=3, sticky="w", padx=5)

        # Duration
        ctk.CTkLabel(
            datetime_frame,
            text="Duration:",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=1, column=0, padx=5, pady=(10, 0))

        duration_options = [text for text, _ in self.DURATIONS]
        self.duration_var = ctk.StringVar()
        self.duration_menu = ctk.CTkOptionMenu(
            datetime_frame,
            values=duration_options,
            variable=self.duration_var,
            width=100,
        )
        self.duration_menu.grid(row=1, column=1, sticky="w", padx=5, pady=(10, 0))
        self.duration_var.set(duration_options[2])  # Default to 2 hours

    def _create_party_details_section(self):
        """Create party size section"""
        section = ctk.CTkFrame(self.content)
        section.pack(fill="x", pady=10)

        ctk.CTkLabel(
            section,
            text="Party Details",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=10, pady=5, anchor="w")

        details_frame = ctk.CTkFrame(section, fg_color="transparent")
        details_frame.pack(fill="x", padx=10, pady=5)

        # Party Size
        ctk.CTkLabel(
            details_frame,
            text="Party Size:",
            font=ctk.CTkFont(weight="bold"),
        ).pack(side="left", padx=5)

        self.party_size_var = ctk.StringVar(value="2")
        party_size = ctk.CTkEntry(
            details_frame,
            textvariable=self.party_size_var,
            width=100,
        )
        party_size.pack(side="left", padx=5)

        # Check Tables Button
        ctk.CTkButton(
            details_frame,
            text="Find Available Tables",
            command=self._check_available_tables,
            width=150,
        ).pack(side="right", padx=5)

    def _create_tables_section(self):
        """Create tables selection section"""
        section = ctk.CTkFrame(self.content)
        section.pack(fill="x", pady=10)

        ctk.CTkLabel(
            section,
            text="Table Selection",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=10, pady=5, anchor="w")

        # Tables Frame
        self.tables_frame = ctk.CTkScrollableFrame(section, height=150)
        self.tables_frame.pack(fill="x", padx=10, pady=5)

    def _create_additional_details_section(self):
        """Create additional details section"""
        section = ctk.CTkFrame(self.content)
        section.pack(fill="x", pady=10)

        ctk.CTkLabel(
            section,
            text="Additional Details",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=10, pady=5, anchor="w")

        # Priority Selection
        priority_frame = ctk.CTkFrame(section, fg_color="transparent")
        priority_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            priority_frame,
            text="Priority:",
            font=ctk.CTkFont(weight="bold"),
        ).pack(side="left", padx=5)

        self.priority_var = ctk.StringVar(value=ReservationPriority.MEDIUM.value)
        priority_menu = ctk.CTkOptionMenu(
            priority_frame,
            values=[p.value for p in ReservationPriority],
            variable=self.priority_var,
            width=150,
        )
        priority_menu.pack(side="left", padx=5)

        # Notes and Requests
        notes_frame = ctk.CTkFrame(section, fg_color="transparent")
        notes_frame.pack(fill="x", padx=10, pady=5)
        notes_frame.grid_columnconfigure((0, 1), weight=1)

        # Notes
        ctk.CTkLabel(
            notes_frame,
            text="Notes:",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.notes_text = ctk.CTkTextbox(notes_frame, height=60)
        self.notes_text.grid(row=1, column=0, sticky="ew", padx=5)

        # Special Requests
        ctk.CTkLabel(
            notes_frame,
            text="Special Requests:",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        self.requests_text = ctk.CTkTextbox(notes_frame, height=60)
        self.requests_text.grid(row=1, column=1, sticky="ew", padx=5)

    def _create_button_section(self):
        """Create bottom buttons section"""
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            width=100,
            fg_color="gray",
            hover_color="darkgray",
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Save",
            command=self.save,
            width=100,
        ).pack(side="right", padx=5)

    def _set_initial_datetime(self):
        """Set initial date and time values"""
        # Set date
        self.date_entry.set_date(self.initial_datetime.date())

        # Round time to nearest slot
        current_time = self.initial_datetime.replace(second=0, microsecond=0)
        minutes = current_time.hour * 60 + current_time.minute
        slot_minutes = 15
        rounded_minutes = ((minutes + slot_minutes - 1) // slot_minutes) * slot_minutes
        rounded_time = current_time.replace(
            hour=rounded_minutes // 60, minute=rounded_minutes % 60
        )

        # Set time
        self.time_var.set(rounded_time.strftime("%H:%M"))

    def _on_customer_search(self, *args):
        """Handle customer search"""
        search_text = self.customer_search.get().strip()

        # Clear previous results
        for widget in self.customer_results.winfo_children():
            widget.destroy()

        if search_text:
            customers = self.customer_service.search_customers(search_text)

            if not customers:
                ctk.CTkLabel(
                    self.customer_results,
                    text="No customers found",
                    text_color="gray",
                ).pack(pady=10)
                return

            for customer in customers:
                customer_frame = ctk.CTkFrame(
                    self.customer_results, fg_color="transparent"
                )
                customer_frame.pack(fill="x", padx=2, pady=1)

                info_text = f"{customer.name} - {customer.phone}"
                if customer.email:
                    info_text += f" - {customer.email}"

                ctk.CTkLabel(
                    customer_frame,
                    text=info_text,
                    font=ctk.CTkFont(size=12),
                ).pack(side="left", padx=5)

                ctk.CTkButton(
                    customer_frame,
                    text="Select",
                    width=60,
                    height=24,
                    command=lambda c=customer: self._select_customer(c),
                ).pack(side="right", padx=5)

    def _select_customer(self, customer):
        """Handle customer selection"""
        self.selected_customer = customer
        self.customer_search.set(f"{customer.name} - {customer.phone}")

        # Clear customer list
        for widget in self.customer_results.winfo_children():
            widget.destroy()

    def _check_available_tables(self):
        """Check and display available tables"""
        try:
            # Get selected date and time
            selected_date = self.date_entry.get_date()
            selected_time = datetime.strptime(self.time_var.get(), "%H:%M").time()
            reservation_datetime = datetime.combine(selected_date, selected_time)

            # Get selected duration
            duration = next(
                duration
                for text, duration in self.DURATIONS
                if text == self.duration_var.get()
            )

            # Validate party size
            if not self.party_size_var.get().isdigit():
                raise ValueError("Please enter a valid party size")
            party_size = int(self.party_size_var.get())
            if party_size <= 0:
                raise ValueError("Party size must be greater than 0")

            # Get available table combinations
            table_combinations = self.table_service.get_available_tables(
                reservation_datetime, duration, party_size
            )

            # Display available combinations
            self._display_table_combinations(table_combinations)

        except Exception as e:
            self._show_error("Error", str(e))

    def _display_table_combinations(self, combinations: List[List[Table]]):
        """Display available table combinations"""
        # Clear previous display
        for widget in self.tables_frame.winfo_children():
            widget.destroy()

        if not combinations:
            ctk.CTkLabel(
                self.tables_frame,
                text="No suitable tables available for selected criteria",
                text_color="red",
                font=ctk.CTkFont(size=12),
            ).pack(pady=10)
            return

        # Display each combination
        for i, tables in enumerate(combinations):
            combo_frame = ctk.CTkFrame(self.tables_frame, fg_color="transparent")
            combo_frame.pack(fill="x", padx=5, pady=2)

            # Calculate total capacity
            total_capacity = sum(table.capacity for table in tables)

            # Create description
            table_desc = ", ".join(
                f"Table {table.number} ({table.capacity} seats)" for table in tables
            )
            desc = f"Option {i+1}: {table_desc} - Total Capacity: {total_capacity}"

            var = ctk.BooleanVar(value=tables == self.selected_tables)
            checkbox = ctk.CTkCheckBox(
                combo_frame,
                text=desc,
                variable=var,
                command=lambda t=tables, v=var: self._on_table_selection(t, v),
            )
            checkbox.pack(side="left", padx=5)

    def _on_table_selection(self, tables: List[Table], var: ctk.BooleanVar):
        """Handle table selection/deselection"""
        if var.get():
            # Deselect other combinations
            for widget in self.tables_frame.winfo_children():
                checkbox = next(
                    (
                        w
                        for w in widget.winfo_children()
                        if isinstance(w, ctk.CTkCheckBox)
                    ),
                    None,
                )
                if checkbox and checkbox.cget("variable") != var:
                    checkbox.deselect()
            self.selected_tables = tables
        else:
            self.selected_tables = []

    def validate(self) -> bool:
        """Validate form inputs"""
        try:
            if not self.selected_customer:
                raise ValueError("Please select a customer")

            if not self.party_size_var.get().isdigit():
                raise ValueError("Please enter a valid party size")
            party_size = int(self.party_size_var.get())
            if party_size <= 0:
                raise ValueError("Party size must be greater than 0")

            if not self.selected_tables:
                raise ValueError("Please select table(s) for the reservation")

            selected_date = self.date_entry.get_date()
            selected_time = datetime.strptime(self.time_var.get(), "%H:%M").time()
            reservation_datetime = datetime.combine(selected_date, selected_time)
            if reservation_datetime < datetime.now():
                raise ValueError("Reservation time cannot be in the past")

            return True

        except ValueError as e:
            self._show_error("Validation Error", str(e))
            return False

    def get_form_data(self) -> dict:
        """Get form data as dictionary"""
        # Get selected duration
        duration = next(
            duration
            for text, duration in self.DURATIONS
            if text == self.duration_var.get()
        )

        # Get datetime
        selected_date = self.date_entry.get_date()
        selected_time = datetime.strptime(self.time_var.get(), "%H:%M").time()
        reservation_datetime = datetime.combine(selected_date, selected_time)

        return {
            "customer_id": self.selected_customer.id,
            "reservation_datetime": reservation_datetime,
            "party_size": int(self.party_size_var.get()),
            "duration": duration,
            "table_ids": [table.id for table in self.selected_tables],
            "priority": ReservationPriority(self.priority_var.get()),
            "notes": self.notes_text.get("0.0", "end").strip() or None,
            "special_requests": self.requests_text.get("0.0", "end").strip() or None,
        }

    def save(self):
        """Save the reservation data"""
        try:
            if self.validate():
                self.result = self.get_form_data()
                self.destroy()
        except Exception as e:
            logger.error(f"Error saving reservation: {e}")
            self._show_error("Error", str(e))

    def fill_fields(self, reservation: Reservation):
        """Fill form fields with reservation data"""
        # Customer
        self.selected_customer = reservation.customer
        self.customer_search.set(
            f"{reservation.customer.name} - {reservation.customer.phone}"
        )

        # Date and time
        self.date_entry.set_date(reservation.reservation_datetime.date())
        self.time_var.set(reservation.reservation_datetime.strftime("%H:%M"))

        # Duration
        for text, value in self.DURATIONS:
            if value == reservation.duration:
                self.duration_var.set(text)
                break

        # Party size
        self.party_size_var.set(str(reservation.party_size))

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
