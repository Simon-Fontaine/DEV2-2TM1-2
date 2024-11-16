from typing import TYPE_CHECKING
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped, validates

from .base import Base

if TYPE_CHECKING:
    from .order import Order
    from .menu_item import MenuItem


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    menu_item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"))
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price: Mapped[float]  # Price at time of order
    notes: Mapped[str] = mapped_column(String(200), nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    menu_item: Mapped["MenuItem"] = relationship(back_populates="order_items")

    @validates("quantity")
    def validate_quantity(self, key, value):
        if value <= 0:
            raise ValueError("Quantity must be greater than 0")
        return value

    def get_subtotal(self) -> float:
        """Calculate the subtotal for this item"""
        return self.quantity * self.unit_price

    def __repr__(self) -> str:
        return f"<OrderItem(menu_item={self.menu_item_id}, quantity={self.quantity})>"
