from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from .base_service import BaseService, handle_db_operation
from ..models.menu_item import MenuItem, MenuItemCategory


class MenuItemService(BaseService[MenuItem]):
    """Service for managing menu items"""

    @handle_db_operation("search_items")
    def search_items(self, session: Session, query: str) -> List[MenuItem]:
        """Search menu items by name or description"""
        return (
            session.query(self.model)
            .filter(
                or_(
                    self.model.name.ilike(f"%{query}%"),
                    self.model.description.ilike(f"%{query}%"),
                )
            )
            .all()
        )

    @handle_db_operation("get_by_category")
    def get_by_category(
        self, session: Session, category: MenuItemCategory
    ) -> List[MenuItem]:
        """Get menu items by category"""
        return (
            session.query(self.model)
            .filter(self.model.category == category)
            .order_by(self.model.name)
            .all()
        )

    @handle_db_operation("update_availability")
    def update_availability(
        self, session: Session, item_id: int, is_available: bool
    ) -> Optional[MenuItem]:
        """Update menu item availability"""
        item = session.query(self.model).get(item_id)
        if item:
            item.is_available = is_available
            return item
        return None

    @handle_db_operation("get_available_items")
    def get_available_items(self, session: Session) -> List[MenuItem]:
        """Get all available menu items"""
        return (
            session.query(self.model)
            .filter(self.model.is_available == True)
            .order_by(self.model.category, self.model.name)
            .all()
        )

    @handle_db_operation("bulk_update_prices")
    def bulk_update_prices(
        self, session: Session, updates: List[tuple[int, float]]
    ) -> int:
        """Update prices for multiple items"""
        updated = 0
        for item_id, new_price in updates:
            if new_price < 0:
                raise ValueError(f"Price cannot be negative for item {item_id}")
            item = session.query(self.model).get(item_id)
            if item:
                item.price = new_price
                updated += 1
        return updated
