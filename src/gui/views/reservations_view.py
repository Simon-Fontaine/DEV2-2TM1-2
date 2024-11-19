import logging
from typing import Dict, Optional
import customtkinter as ctk
from datetime import datetime, timedelta
from tkcalendar import Calendar

from .base_view import BaseView
from ..dialogs.reservation_dialog import ReservationDialog
from ...models.reservation import Reservation, ReservationStatus
from ...services.reservation_service import ReservationService
from ...services.customer_service import CustomerService
from ...services.table_service import TableService

logger = logging.getLogger(__name__)


class ReservationsView(BaseView[Reservation]):
    """View for managing reservations"""

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
        """Initialize the UI components"""
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._create_header()
        self._create_main_content()

    def _create_header(self):
        """Create header with title and controls"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="ew")
        header.grid_columnconfigure(2, weight=1)

        # Title
        ctk.CTkLabel(
            header,
            text="Reservations Management",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=10)

        # New Reservation button
        ctk.CTkButton(
            header,
            text="New Reservation",
            width=120,
            command=self._handle_new_reservation,
        ).grid(row=0, column=1, padx=10, pady=10)

        # Refresh button
        ctk.CTkButton(header, text="Refresh", width=100, command=self.refresh).grid(
            row=0, column=2, sticky="e", padx=10, pady=10
        )

    def _create_main_content(self):
        """Create main content area with calendar and reservations list"""
        # Left side - Calendar
        calendar_frame = ctk.CTkFrame(self)
        calendar_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        self.calendar = Calendar(
            calendar_frame,
            selectmode="day",
            date_pattern="y-mm-dd",
            background="darkblue",
            foreground="white",
            borderwidth=2,
        )
        self.calendar.pack(padx=10, pady=10)
        self.calendar.bind("<<CalendarSelected>>", self._on_date_selected)

        # Right side - Reservations list
        reservations_frame = ctk.CTkFrame(self)
        reservations_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        reservations_frame.grid_rowconfigure(1, weight=1)
        reservations_frame.grid_columnconfigure(0, weight=1)

        # Filters
        filters_frame = ctk.CTkFrame(reservations_frame, fg_color="transparent")
        filters_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Status filter
        status_frame = ctk.CTkFrame(filters_frame, fg_color="transparent")
        status_frame.pack(side="left", padx=5)

        ctk.CTkLabel(status_frame, text="Status:").pack(side="left", padx=5)

        self.status_var = ctk.StringVar(value="All")
        status_menu = ctk.CTkOptionMenu(
            status_frame,
            values=["All"] + [status.value for status in ReservationStatus],
            variable=self.status_var,
            command=self._apply_filters,
            width=120,
        )
        status_menu.pack(side="left", padx=5)

        # Reservations list
        self.reservations_list = ctk.CTkScrollableFrame(reservations_frame)
        self.reservations_list.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def refresh(self):
        """Refresh the reservations display"""
        try:
            # Get selected date
            selected_date = self.calendar.selection_get()
            start_date = datetime.combine(selected_date, datetime.min.time())
            end_date = start_date + timedelta(days=1)

            # Get reservations
            selected_status = self.status_var.get()
            status = (
                ReservationStatus(selected_status) if selected_status != "All" else None
            )

            reservations = self.service.search_reservations(
                start_date=start_date, end_date=end_date, status=status
            )

            # Clear current display
            for widget in self.reservations_list.winfo_children():
                widget.destroy()

            if not reservations:
                ctk.CTkLabel(
                    self.reservations_list,
                    text="No reservations found",
                    text_color="gray",
                ).pack(pady=20)
                return

            # Display reservations
            for reservation in sorted(
                reservations, key=lambda r: r.reservation_datetime
            ):
                self._create_reservation_card(reservation)

        except Exception as e:
            logger.error(f"Error refreshing reservations: {e}")
            self.show_error("Error", f"Failed to refresh reservations: {str(e)}")

    def _create_reservation_card(self, reservation: Reservation):
        """Create a card displaying reservation information"""
        card = ctk.CTkFrame(self.reservations_list)
        card.pack(fill="x", padx=5, pady=2)
        card.grid_columnconfigure(1, weight=1)

        # Time and customer info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        time_str = reservation.reservation_datetime.strftime("%H:%M")
        end_time = reservation.get_end_time().strftime("%H:%M")

        ctk.CTkLabel(
            info_frame,
            text=f"{time_str} - {end_time}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        ctk.CTkLabel(info_frame, text=f"•", font=ctk.CTkFont(size=14)).pack(
            side="left", padx=5
        )

        ctk.CTkLabel(
            info_frame, text=f"{reservation.customer.name}", font=ctk.CTkFont(size=14)
        ).pack(side="left")

        # Status tag
        status_frame = ctk.CTkFrame(
            info_frame, fg_color=self._get_status_color(reservation.status)
        )
        status_frame.pack(side="right")

        ctk.CTkLabel(
            status_frame,
            text=reservation.status.value,
            text_color="white",
            font=ctk.CTkFont(size=12),
        ).pack(padx=5, pady=2)

        # Details
        details_frame = ctk.CTkFrame(card, fg_color="transparent")
        details_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)

        details = [
            f"Party: {reservation.party_size}",
            f"Duration: {reservation.duration} min",
            f"Tables: {', '.join(str(t.number) for t in reservation.tables)}",
        ]

        ctk.CTkLabel(
            details_frame, text=" | ".join(details), font=ctk.CTkFont(size=12)
        ).pack(side="left")

        # Action buttons
        actions_frame = ctk.CTkFrame(card, fg_color="transparent")
        actions_frame.grid(row=1, column=1, sticky="e", padx=10, pady=5)

        # Create different action buttons based on reservation status
        if reservation.status == ReservationStatus.PENDING:
            ctk.CTkButton(
                actions_frame,
                text="Confirm",
                width=80,
                height=28,
                command=lambda r=reservation: self._handle_confirm_reservation(r),
            ).pack(side="right", padx=2)

        elif reservation.status == ReservationStatus.CONFIRMED:
            # Check-in button
            if reservation.is_active():
                ctk.CTkButton(
                    actions_frame,
                    text="Check In",
                    width=80,
                    height=28,
                    command=lambda r=reservation: self._handle_check_in(r),
                ).pack(side="right", padx=2)

            # No-show button (only for past reservations)
            elif reservation.reservation_datetime < datetime.now():
                ctk.CTkButton(
                    actions_frame,
                    text="No Show",
                    width=80,
                    height=28,
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda r=reservation: self._handle_no_show(r),
                ).pack(side="right", padx=2)

        elif reservation.status == ReservationStatus.CHECKED_IN:
            ctk.CTkButton(
                actions_frame,
                text="Complete",
                width=80,
                height=28,
                command=lambda r=reservation: self._handle_complete_reservation(r),
            ).pack(side="right", padx=2)

        # Cancel button (for pending/confirmed reservations)
        if reservation.can_cancel():
            ctk.CTkButton(
                actions_frame,
                text="Cancel",
                width=80,
                height=28,
                fg_color="red",
                hover_color="darkred",
                command=lambda r=reservation: self._handle_cancel_reservation(r),
            ).pack(side="right", padx=2)

        # Notes/Requests (if any)
        if reservation.notes or reservation.special_requests:
            notes_frame = ctk.CTkFrame(card, fg_color="transparent")
            notes_frame.grid(
                row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5
            )

            if reservation.notes:
                ctk.CTkLabel(
                    notes_frame,
                    text=f"Notes: {reservation.notes}",
                    font=ctk.CTkFont(size=12),
                    text_color="gray",
                ).pack(side="left", padx=(0, 10))

            if reservation.special_requests:
                ctk.CTkLabel(
                    notes_frame,
                    text=f"Special Requests: {reservation.special_requests}",
                    font=ctk.CTkFont(size=12),
                    text_color="orange",
                ).pack(side="left")

    def _get_status_color(self, status: ReservationStatus) -> str:
        """Get color for reservation status"""
        colors = {
            ReservationStatus.PENDING: "#FFA726",  # Orange
            ReservationStatus.CONFIRMED: "#42A5F5",  # Blue
            ReservationStatus.CHECKED_IN: "#66BB6A",  # Green
            ReservationStatus.COMPLETED: "#26A69A",  # Teal
            ReservationStatus.CANCELLED: "#EF5350",  # Red
            ReservationStatus.NO_SHOW: "#EC407A",  # Pink
        }
        return colors.get(status, "#9E9E9E")  # Default gray

    def _on_date_selected(self, event):
        """Handle date selection in calendar"""
        self.refresh()

    def _apply_filters(self, *args):
        """Apply filters and refresh display"""
        self.refresh()

    def _handle_new_reservation(self):
        """Handle creating a new reservation"""
        try:
            dialog = ReservationDialog(self, self.customer_service, self.table_service)
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
            updated = self.service.update(
                reservation.id, status=ReservationStatus.CONFIRMED
            )
            if updated:
                self.refresh()
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
            logger.error(f"Error checking in reservation: {e}")
            self.show_error("Error", f"Failed to check in: {str(e)}")

    def _handle_complete_reservation(self, reservation: Reservation):
        """Handle completing a checked-in reservation"""
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
