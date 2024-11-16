from enum import Enum
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Enum as SQLEnum
from sqlalchemy.orm import relationship, mapped_column, Mapped, validates

from .base import Base

if TYPE_CHECKING:
    from .order_item import OrderItem


class MenuItemCategory(str, Enum):
    APPETIZER = "Appetizer"
    MAIN_COURSE = "Main Course"
    DESSERT = "Dessert"
    BEVERAGE = "Beverage"
    SPECIAL = "Special"
    SIDE_DISH = "Side Dish"


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[MenuItemCategory] = mapped_column(SQLEnum(MenuItemCategory))
    price: Mapped[float]
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    is_available: Mapped[bool] = mapped_column(default=True)
    preparation_time: Mapped[int] = mapped_column(default=15)  # in minutes
    allergens: Mapped[str] = mapped_column(String(200), nullable=True)

    # Relationships
    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="menu_item", cascade="all, delete-orphan"
    )

    @validates("price")
    def validate_price(self, key, value):
        if value < 0:
            raise ValueError("Price cannot be negative")
        return value

    @validates("preparation_time")
    def validate_prep_time(self, key, value):
        if value < 0:
            raise ValueError("Preparation time cannot be negative")
        return value

    def __repr__(self) -> str:
        return f"<MenuItem(name='{self.name}', category={self.category.value}, price=${self.price:.2f})>"
