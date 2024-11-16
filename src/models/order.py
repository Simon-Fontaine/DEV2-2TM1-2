from enum import Enum
from typing import List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, mapped_column, Mapped
from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum

from .base import Base

if TYPE_CHECKING:
    from .customer import Customer
    from .table import Table
    from .order_item import OrderItem


class OrderStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    PAID = "Paid"


class PaymentMethod(str, Enum):
    CASH = "Cash"
    CREDIT_CARD = "Credit Card"
    DEBIT_CARD = "Debit Card"
    MOBILE_PAYMENT = "Mobile Payment"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("tables.id"))
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=True)
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str] = mapped_column(String(500), nullable=True)

    # Payment information
    total_amount: Mapped[float] = mapped_column(default=0.0)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod), nullable=True
    )
    is_paid: Mapped[bool] = mapped_column(default=False)

    # Relationships
    table: Mapped["Table"] = relationship(back_populates="orders")
    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )

    def calculate_total(self) -> float:
        """Calculate the total amount of the order"""
        return sum(item.quantity * item.unit_price for item in self.items)

    def update_status(self, new_status: OrderStatus) -> None:
        """Update order status with proper timestamps"""
        self.status = new_status
        if new_status == OrderStatus.COMPLETED:
            self.completed_at = datetime.now()

    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id}, table={self.table_id}, status={self.status.value})>"
        )
