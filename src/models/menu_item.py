from sqlalchemy import Column, Integer, String, Float, Boolean, CheckConstraint
from sqlalchemy.orm import relationship, validates
from enum import Enum
from models.base import Base


class MenuCategory(Enum):
    APPETIZER = "Appetizer"
    MAIN_COURSE = "Main Course"
    DESSERT = "Dessert"
    BEVERAGE = "Beverage"


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    is_available = Column(Boolean, default=True, nullable=False)

    orders = relationship(
        "OrderItem", back_populates="menu_item", cascade="all, delete-orphan"
    )

    __table_args__ = (CheckConstraint("price >= 0", name="check_price_non_negative"),)

    @validates("name")
    def validate_name(self, key, value):
        if not value.strip():
            raise ValueError("Menu item name cannot be empty.")
        return value

    @validates("category")
    def validate_category(self, key, value):
        if value not in [category.value for category in MenuCategory]:
            raise ValueError(
                f"Invalid category. Must be one of {[c.value for c in MenuCategory]}."
            )
        return value

    @validates("price")
    def validate_price(self, key, value):
        if value < 0:
            raise ValueError("Price cannot be negative.")
        return value

    def __repr__(self):
        return (
            f"<MenuItem(id={self.id}, name={self.name}, category={self.category}, "
            f"price={self.price}, is_available={self.is_available})>"
        )
