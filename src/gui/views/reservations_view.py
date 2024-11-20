import logging
from typing import Dict, Optional, List
import customtkinter as ctk
from datetime import datetime, timedelta
from tkcalendar import Calendar

from .base_view import BaseView
from ..dialogs.reservation_dialog import ReservationDialog
from ...models.reservation import Reservation, ReservationStatus, ReservationPriority
from ...services.reservation_service import ReservationService
from ...services.customer_service import CustomerService
from ...services.table_service import TableService

logger = logging.getLogger(__name__)


class ReservationsView(BaseView[Reservation]):
    """Optimized view for managing reservations"""

    def __init__(
        self,
        master: any,
        reservation_service: ReservationService,
        customer_service: CustomerService,
        table_service: TableService,
    ):
        self.customer_service = customer_service
        self.table_service = table_service
        self.reservations: Dict[int, Reservation] = {}
        super().__init__(master, reservation_service)
        self.refresh()

    def initialize_ui(self):
        """Initialize the UI components with improved layout and fixed sidebar width"""
        # Configure grid weights for full window utilization
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Changed to 0 to prevent expansion
        self.grid_columnconfigure(1, weight=1)  # Main content area expands

        self._create_header()
        self._create_main_content()

    def _create_header(self):
        """Create header with improved styling"""
        header = ctk.CTkFrame(self)
        header.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")
        header.grid_columnconfigure(2, weight=1)

        # Title with larger font
        ctk.CTkLabel(
            header,
            text="Reservations Management",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=10)

        # Add Summary Statistics
        self.stats_frame = ctk.CTkFrame(header, fg_color="transparent")
        self.stats_frame.grid(row=0, column=1, padx=20, sticky="w")
        self._update_stats()

        # Controls
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.grid(row=0, column=2, padx=20, sticky="e")

        ctk.CTkButton(
            controls,
            text="New Reservation",
            width=150,
            height=40,
            command=self._handle_new_reservation,
            font=ctk.CTkFont(size=14),
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            controls,
            text="Refresh",
            width=100,
            height=40,
            command=self.refresh,
            font=ctk.CTkFont(size=14),
        ).pack(side="right", padx=10)

    def _create_main_content(self):
        """Create main content area with fixed sidebar width"""
        # Left side - Calendar and Filters with fixed width
        left_panel = ctk.CTkFrame(self, width=300)  # Fixed width
        left_panel.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        left_panel.grid_propagate(False)  # Prevent grid from changing the width
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_rowconfigure(2, weight=1)

        # Calendar section
        calendar_frame = ctk.CTkFrame(left_panel)
        calendar_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(
            calendar_frame,
            text="Select Date",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(10, 5))

        self.calendar = Calendar(
            calendar_frame,
            selectmode="day",
            date_pattern="y-mm-dd",
            background="#1f1f1f",
            foreground="white",
            headersbackground="#2d2d2d",
            headersforeground="white",
            selectbackground="#2196F3",
            normalbackground="#2d2d2d",
            normalforeground="white",
            weekendbackground="#333333",
            weekendforeground="white",
            othermonthbackground="#1a1a1a",
            othermonthforeground="gray",
            borderwidth=0,
            width=20,  # Set calendar width
            height=8,  # Set calendar height
        )
        self.calendar.pack(padx=10, pady=10, fill="x")
        self.calendar.bind("<<CalendarSelected>>", self._on_date_selected)

        # Filters section
        filters_frame = ctk.CTkFrame(left_panel)
        filters_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(
            filters_frame,
            text="Filters",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(10, 5))

        # Status filter
        status_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=10, pady=5)
        status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            status_frame,
            text="Status:",
            font=ctk.CTkFont(weight="bold"),
        ).pack(side="left")

        self.status_var = ctk.StringVar(value="All")
        status_menu = ctk.CTkOptionMenu(
            status_frame,
            values=["All"] + [status.value for status in ReservationStatus],
            variable=self.status_var,
            command=self._apply_filters,
            width=180,  # Fixed width for dropdown
        )
        status_menu.pack(side="right")

        # Time slots filter
        time_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        time_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            time_frame,
            text="Time:",
            font=ctk.CTkFont(weight="bold"),
        ).pack(side="left")

        self.time_filter = ctk.StringVar(value="All Day")
        time_menu = ctk.CTkOptionMenu(
            time_frame,
            values=["All Day", "Morning", "Afternoon", "Evening"],
            variable=self.time_filter,
            command=self._apply_filters,
            width=180,  # Fixed width for dropdown
        )
        time_menu.pack(side="right")

        # Quick navigation buttons
        nav_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10, pady=10)

        # Distribute buttons evenly
        button_width = 85  # Fixed width for buttons
        button_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        button_frame.pack(expand=True)

        ctk.CTkButton(
            button_frame,
            text="Today",
            command=lambda: self._quick_nav(0),
            width=button_width,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            button_frame,
            text="Tomorrow",
            command=lambda: self._quick_nav(1),
            width=button_width,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            button_frame,
            text="Next Week",
            command=lambda: self._quick_nav(7),
            width=button_width,
        ).pack(side="left", padx=2)

        # Right side - Reservations List
        right_panel = ctk.CTkFrame(self)
        right_panel.grid(row=1, column=1, padx=(0, 20), pady=10, sticky="nsew")
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # Reservations header
        header_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        self.date_label = ctk.CTkLabel(
            header_frame,
            text="",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.date_label.pack(side="left")

        # Reservations list
        self.reservations_list = ctk.CTkScrollableFrame(right_panel)
        self.reservations_list.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.reservations_list.grid_columnconfigure(0, weight=1)

    def _update_stats(self):
        """Update reservation statistics display"""
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)

            # Get counts
            today_count = len(
                self.service.search_reservations(
                    start_date=datetime.combine(today, datetime.min.time()),
                    end_date=datetime.combine(today, datetime.max.time()),
                )
            )

            upcoming_count = len(self.service.get_upcoming_reservations())

            # Update labels
            for widget in self.stats_frame.winfo_children():
                widget.destroy()

            ctk.CTkLabel(
                self.stats_frame,
                text=f"Today: {today_count}",
                font=ctk.CTkFont(size=14),
            ).pack(side="left", padx=10)

            ctk.CTkLabel(
                self.stats_frame,
                text=f"Upcoming: {upcoming_count}",
                font=ctk.CTkFont(size=14),
            ).pack(side="left", padx=10)

        except Exception as e:
            logger.error(f"Error updating statistics: {e}")

    def _create_reservation_card(self, reservation: Reservation) -> ctk.CTkFrame:
        """Create an improved reservation card with status indicators"""
        card = ctk.CTkFrame(self.reservations_list)
        card.pack(fill="x", padx=5, pady=2)

        # Status indicator
        status_color = self._get_status_color(reservation.status)
        indicator = ctk.CTkFrame(card, width=4, fg_color=status_color)
        indicator.pack(side="left", fill="y")

        # Main content
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # Header row
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")

        # Time and customer info
        time_str = reservation.reservation_datetime.strftime("%H:%M")
        end_time = reservation.get_end_time().strftime("%H:%M")

        # Add status-specific indicators
        status_text = time_str
        if reservation.status == ReservationStatus.PENDING:
            status_text = "⏳ " + status_text  # Pending indicator
        elif reservation.status == ReservationStatus.CONFIRMED:
            if reservation.can_check_in():
                status_text = "✓ " + status_text  # Ready for check-in
            elif reservation.is_late():
                status_text = "⚠️ " + status_text  # Late indicator
        elif reservation.status == ReservationStatus.CHECKED_IN:
            status_text = "👥 " + status_text  # Checked in indicator

        time_label = ctk.CTkLabel(
            header,
            text=f"{status_text} - {end_time}",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        time_label.pack(side="left")

        customer_label = ctk.CTkLabel(
            header,
            text=f"• {reservation.customer.name}",
            font=ctk.CTkFont(size=14),
        )
        customer_label.pack(side="left", padx=10)

        # Contact info
        contact_frame = ctk.CTkFrame(header, fg_color="transparent")
        contact_frame.pack(side="left", padx=10)

        if reservation.customer.phone:
            phone_label = ctk.CTkLabel(
                contact_frame,
                text=f"📞 {reservation.customer.phone}",
                font=ctk.CTkFont(size=12),
                text_color="gray",
            )
            phone_label.pack(side="left", padx=5)

        if reservation.customer.email:
            email_label = ctk.CTkLabel(
                contact_frame,
                text=f"📧 {reservation.customer.email}",
                font=ctk.CTkFont(size=12),
                text_color="gray",
            )
            email_label.pack(side="left", padx=5)

        # Status tag
        status_frame = ctk.CTkFrame(header, fg_color=status_color)
        status_frame.pack(side="right")

        status_text = reservation.status.value
        if reservation.status == ReservationStatus.CONFIRMED and reservation.is_late():
            status_text += " (Late)"

        ctk.CTkLabel(
            status_frame,
            text=status_text,
            text_color="white",
            font=ctk.CTkFont(size=12),
        ).pack(padx=5, pady=2)

        # Details row
        details = ctk.CTkFrame(content, fg_color="transparent")
        details.pack(fill="x", pady=(5, 0))

        details_text = [
            f"Party: {reservation.party_size}",
            f"Duration: {reservation.duration} min",
            f"Tables: {', '.join(str(t.number) for t in reservation.tables)}",
        ]

        if reservation.priority != ReservationPriority.MEDIUM:
            details_text.append(f"Priority: {reservation.priority.value}")

        if reservation.notes or reservation.special_requests:
            details_text.append("📝")  # Note indicator

        ctk.CTkLabel(
            details,
            text=" | ".join(details_text),
            font=ctk.CTkFont(size=12),
        ).pack(side="left")

        # Action buttons
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.pack(fill="x", pady=(5, 0))

        self._create_action_buttons(actions, reservation)

        # Notes/Requests (if any)
        if reservation.notes or reservation.special_requests:
            notes = ctk.CTkFrame(content, fg_color="transparent")
            notes.pack(fill="x", pady=(5, 0))

            if reservation.notes:
                notes_frame = ctk.CTkFrame(notes, fg_color="#2d2d2d")
                notes_frame.pack(fill="x", pady=2)
                ctk.CTkLabel(
                    notes_frame,
                    text="📝 Notes:",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="gray",
                ).pack(side="left", padx=5)
                ctk.CTkLabel(
                    notes_frame,
                    text=reservation.notes,
                    font=ctk.CTkFont(size=12),
                    text_color="gray",
                    wraplength=600,
                ).pack(side="left", padx=5, pady=2)

            if reservation.special_requests:
                requests_frame = ctk.CTkFrame(notes, fg_color="#2d2d2d")
                requests_frame.pack(fill="x", pady=2)
                ctk.CTkLabel(
                    requests_frame,
                    text="⚠️ Special Requests:",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="orange",
                ).pack(side="left", padx=5)
                ctk.CTkLabel(
                    requests_frame,
                    text=reservation.special_requests,
                    font=ctk.CTkFont(size=12),
                    text_color="orange",
                    wraplength=600,
                ).pack(side="left", padx=5, pady=2)

        return card

    def _create_action_buttons(self, parent: ctk.CTkFrame, reservation: Reservation):
        if reservation.status == ReservationStatus.PENDING:
            ctk.CTkButton(
                parent,
                text="Confirm",
                width=80,
                height=28,
                command=lambda: self._handle_confirm_reservation(reservation),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                parent,
                text="Cancel",
                width=80,
                height=28,
                fg_color="red",
                hover_color="darkred",
                command=lambda: self._handle_cancel_reservation(reservation),
            ).pack(side="left", padx=2)

        elif reservation.status == ReservationStatus.CONFIRMED:
            if reservation.can_check_in():
                ctk.CTkButton(
                    parent,
                    text="Check In",
                    width=80,
                    height=28,
                    command=lambda: self._handle_check_in(reservation),
                ).pack(side="left", padx=2)
            elif reservation.is_late():
                ctk.CTkButton(
                    parent,
                    text="No Show",
                    width=80,
                    height=28,
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda: self._handle_no_show(reservation),
                ).pack(side="left", padx=2)

            if reservation.can_cancel():
                ctk.CTkButton(
                    parent,
                    text="Cancel",
                    width=80,
                    height=28,
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda: self._handle_cancel_reservation(reservation),
                ).pack(side="left", padx=2)
        elif reservation.status == ReservationStatus.CHECKED_IN:
            ctk.CTkButton(
                parent,
                text="Complete",
                width=80,
                height=28,
                command=lambda: self._handle_complete_reservation(reservation),
            ).pack(side="left", padx=2)

    def refresh(self):
        """Refresh the reservations display with reversed order"""
        try:
            # Update date label
            selected_date = self.calendar.selection_get()
            self.date_label.configure(
                text=f"Reservations for {selected_date.strftime('%A, %B %d, %Y')}"
            )

            # Get selected date range
            start_date = datetime.combine(selected_date, datetime.min.time())
            end_date = datetime.combine(selected_date, datetime.max.time())

            # Apply time filter
            time_filter = self.time_filter.get()
            if time_filter == "Morning":
                start_date = start_date.replace(hour=6)
                end_date = start_date.replace(hour=12)
            elif time_filter == "Afternoon":
                start_date = start_date.replace(hour=12)
                end_date = start_date.replace(hour=17)
            elif time_filter == "Evening":
                start_date = start_date.replace(hour=17)
                end_date = start_date.replace(hour=23, minute=59)

            # Get status filter
            selected_status = self.status_var.get()
            status = (
                ReservationStatus(selected_status) if selected_status != "All" else None
            )

            # Get reservations
            reservations = self.service.search_reservations(
                start_date=start_date, end_date=end_date, status=status
            )

            # Clear current display
            for widget in self.reservations_list.winfo_children():
                widget.destroy()

            if not reservations:
                self._show_empty_state()
                return

            # Group reservations by time slot
            time_slots = self._group_reservations_by_time(reservations)

            # Display reservations by time slot in reverse order
            for hour in sorted(time_slots.keys(), reverse=True):
                hour_reservations = time_slots[hour]
                if hour_reservations:
                    # Add time slot header
                    self._create_time_slot_header(hour)

                    # Add reservations for this time slot in reverse chronological order
                    for reservation in sorted(
                        hour_reservations,
                        key=lambda r: r.reservation_datetime,
                        reverse=True,
                    ):
                        self._create_reservation_card(reservation)

            # Update statistics
            self._update_stats()

        except Exception as e:
            logger.error(f"Error refreshing reservations: {e}")
            self.show_error("Error", f"Failed to refresh reservations: {str(e)}")

    def _show_empty_state(self):
        """Show empty state message with style"""
        empty_frame = ctk.CTkFrame(self.reservations_list, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            empty_frame,
            text="No reservations found for this date",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(pady=20)

        ctk.CTkButton(
            empty_frame,
            text="Create New Reservation",
            command=self._handle_new_reservation,
        ).pack()

    def _create_time_slot_header(self, hour: int):
        """Create a styled header for time slots"""
        header = ctk.CTkFrame(self.reservations_list, fg_color="transparent")
        header.pack(fill="x", padx=5, pady=(10, 5))

        time_text = f"{hour:02d}:00"
        ctk.CTkLabel(
            header,
            text=time_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#666666",
        ).pack(side="left")

        separator = ctk.CTkFrame(header, height=1, fg_color="#333333")
        separator.pack(side="left", fill="x", expand=True, padx=10)

    def _group_reservations_by_time(self, reservations) -> Dict[int, List[Reservation]]:
        """Group reservations by hour and sort within each group"""
        time_slots = {}
        for reservation in reservations:
            hour = reservation.reservation_datetime.hour
            if hour not in time_slots:
                time_slots[hour] = []
            time_slots[hour].append(reservation)

        # Sort reservations within each time slot by datetime in reverse order
        for hour in time_slots:
            time_slots[hour].sort(key=lambda r: r.reservation_datetime, reverse=True)

        return time_slots

    def _get_status_color(self, status: ReservationStatus) -> str:
        """Get color for reservation status with improved colors"""
        colors = {
            ReservationStatus.PENDING: "#FFA726",  # Orange
            ReservationStatus.CONFIRMED: "#42A5F5",  # Blue
            ReservationStatus.CHECKED_IN: "#66BB6A",  # Green
            ReservationStatus.COMPLETED: "#26A69A",  # Teal
            ReservationStatus.CANCELLED: "#EF5350",  # Red
            ReservationStatus.NO_SHOW: "#EC407A",  # Pink
        }
        return colors.get(status, "#9E9E9E")  # Default gray

    def _quick_nav(self, days_ahead: int):
        """Quick navigation to specific dates"""
        target_date = datetime.now().date() + timedelta(days=days_ahead)
        self.calendar.selection_set(target_date)
        self._on_date_selected(None)

    def _on_date_selected(self, event):
        """Handle date selection in calendar"""
        self.refresh()

    def _apply_filters(self, *args):
        """Apply filters and refresh display"""
        self.refresh()

    def _handle_new_reservation(self):
        """Handle creating a new reservation with improved error handling"""
        try:
            # Pre-select current calendar date
            initial_datetime = datetime.combine(
                self.calendar.selection_get(),
                datetime.now().time().replace(minute=0, second=0, microsecond=0),
            )

            dialog = ReservationDialog(
                self,
                self.customer_service,
                self.table_service,
                initial_datetime=initial_datetime,
            )

            self.wait_window(dialog)

            if dialog.result:
                self.service.create_reservation(**dialog.result)
                self.refresh()

        except Exception as e:
            logger.error(f"Error creating reservation: {e}")
            self.show_error("Error", f"Failed to create reservation: {str(e)}")

    def _handle_confirm_reservation(self, reservation: Reservation):
        """Handle confirming a pending reservation"""
        try:
            if self.show_confirm(
                "Confirm Reservation",
                f"Confirm reservation for {reservation.customer.name}?\n\n"
                f"Date: {reservation.reservation_datetime.strftime('%Y-%m-%d %H:%M')}\n"
                f"Party Size: {reservation.party_size}\n"
                f"Tables: {', '.join(str(t.number) for t in reservation.tables)}",
            ):
                confirmed = self.service.confirm_reservation(reservation.id)
                if confirmed:
                    self.refresh()
                    self.show_message(
                        "Reservation Confirmed",
                        f"Reservation for {reservation.customer.name} has been confirmed.",
                    )
        except Exception as e:
            logger.error(f"Error confirming reservation: {e}")
            self.show_error("Error", f"Failed to confirm reservation: {str(e)}")

    def _handle_check_in(self, reservation: Reservation):
        """Handle checking in a reservation"""
        try:
            if self.show_confirm(
                "Confirm Check-in",
                f"Check in reservation for {reservation.customer.name}?",
            ):
                self.service.check_in(reservation.id)
                self.refresh()
        except Exception as e:
            logger.error(f"Error checking in: {e}")
            self.show_error("Error", f"Failed to check in: {str(e)}")

    def _handle_complete_reservation(self, reservation: Reservation):
        """Handle completing a reservation"""
        try:
            if self.show_confirm(
                "Complete Reservation",
                f"Mark reservation for {reservation.customer.name} as completed?",
            ):
                self.service.complete_reservation(reservation.id)
                self.refresh()
        except Exception as e:
            logger.error(f"Error completing reservation: {e}")
            self.show_error("Error", f"Failed to complete reservation: {str(e)}")

    def _handle_cancel_reservation(self, reservation: Reservation):
        """Handle cancelling a reservation"""
        try:
            if self.show_confirm(
                "Cancel Reservation",
                f"Are you sure you want to cancel the reservation for {reservation.customer.name}?",
            ):
                self.service.cancel_reservation(reservation.id)
                self.refresh()
        except Exception as e:
            logger.error(f"Error cancelling reservation: {e}")
            self.show_error("Error", f"Failed to cancel reservation: {str(e)}")

    def _handle_no_show(self, reservation: Reservation):
        """Handle marking a reservation as no-show"""
        try:
            if self.show_confirm(
                "Mark No-show",
                f"Mark {reservation.customer.name}'s reservation as no-show?",
            ):
                self.service.mark_no_show(reservation.id)
                self.refresh()
        except Exception as e:
            logger.error(f"Error marking no-show: {e}")
            self.show_error("Error", f"Failed to mark no-show: {str(e)}")

    def show_message(self, title: str, message: str):
        from ..dialogs.message_dialog import CTkMessageDialog

        dialog = CTkMessageDialog(self, title, message)
        dialog.wait_window()
