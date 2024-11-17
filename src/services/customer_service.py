from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from .base_service import BaseService, handle_db_operation
from ..models.customer import Customer
from ..models.reservation import Reservation, ReservationStatus


class CustomerService(BaseService[Customer]):
    """
    Service for managing customer-related operations
    """

    @handle_db_operation("search_customers")
    def search_customers(self, session: Session, query: str) -> List[Customer]:
        """Search customers by name, phone, or email"""
        return (
            session.query(self.model)
            .filter(
                or_(
                    self.model.name.ilike(f"%{query}%"),
                    self.model.phone.ilike(f"%{query}%"),
                    self.model.email.ilike(f"%{query}%"),
                )
            )
            .all()
        )

    @handle_db_operation("get_customer_reservations")
    def get_customer_reservations(
        self, session: Session, customer_id: int, include_past: bool = False
    ) -> List[Reservation]:
        """Get customer's reservations, optionally including past ones"""
        customer = session.query(self.model).get(customer_id)
        if not customer:
            return []

        if include_past:
            return [
                r
                for r in customer.reservations
                if r.status != ReservationStatus.CANCELLED
            ]
        else:
            return customer.get_active_reservations()

    @handle_db_operation("get_customer_by_phone")
    def get_customer_by_phone(self, session: Session, phone: str) -> Optional[Customer]:
        """Get customer by phone number"""
        return session.query(self.model).filter(self.model.phone == phone).first()

    @handle_db_operation("get_customer_by_email")
    def get_customer_by_email(self, session: Session, email: str) -> Optional[Customer]:
        """Get customer by email"""
        return session.query(self.model).filter(self.model.email == email).first()

    @handle_db_operation("update_customer_notes")
    def update_customer_notes(
        self, session: Session, customer_id: int, notes: str
    ) -> Optional[Customer]:
        """Update customer notes"""
        customer = session.query(self.model).get(customer_id)
        if customer:
            customer.notes = notes
            return customer
        return None
