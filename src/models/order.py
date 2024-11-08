from sqlalchemy import Column, Integer, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import relationship, validates
from enum import Enum
from models.base import Base


class OrderStatus(Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    status = Column(
        SQLEnum(OrderStatus, native_enum=False),
        default=OrderStatus.PENDING,
        nullable=False,
    )

    table = relationship("Table", back_populates="orders")
    order_items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')",
            name="check_order_status",
        ),
    )

    @validates("status")
    def validate_status(self, key, value):
        if not isinstance(value, OrderStatus):
            raise ValueError(
                "Invalid order status. Must be an instance of OrderStatus."
            )
        return value

    def __repr__(self):
        return f"<Order(id={self.id}, table_id={self.table_id}, status={self.status.value})>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    order = relationship("Order", back_populates="order_items")
    menu_item = relationship("MenuItem", back_populates="orders")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_order_item_quantity_positive"),
    )

    @validates("quantity")
    def validate_quantity(self, key, value):
        if value <= 0:
            raise ValueError("Quantity must be a positive integer.")
        return value

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, menu_item_id={self.menu_item_id}, quantity={self.quantity})>"
