import logging
from typing import Optional
from models.db import session_scope
from models.menu_item import MenuItem, MenuCategory
from sqlalchemy.exc import IntegrityError


def add_menu_item(
    name: str,
    category: str,
    price: float,
    description: str = "",
    is_available: bool = True,
) -> None:
    with session_scope() as session:
        try:
            menu_category = MenuCategory(category)
        except ValueError:
            logging.error(
                f"Invalid category: {category}. Must be one of {[c.value for c in MenuCategory]}."
            )
            return

        new_item = MenuItem(
            name=name,
            category=menu_category.value,
            price=price,
            description=description,
            is_available=is_available,
        )
        session.add(new_item)
        try:
            session.commit()
            logging.info(
                f"Successfully added Menu Item '{name}' in category '{category}'."
            )
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to add menu item: {e.orig}")


def update_menu_item(
    item_id: int,
    name: Optional[str] = None,
    category: Optional[str] = None,
    price: Optional[float] = None,
    description: Optional[str] = None,
    is_available: Optional[bool] = None,
) -> None:
    with session_scope() as session:
        item = session.query(MenuItem).filter_by(id=item_id).first()
        if not item:
            logging.error(f"Menu Item with ID {item_id} does not exist.")
            return

        if name is not None:
            item.name = name
        if category is not None:
            try:
                menu_category = MenuCategory(category)
                item.category = menu_category.value
            except ValueError:
                logging.error(
                    f"Invalid category: {category}. Must be one of {[c.value for c in MenuCategory]}."
                )
                return
        if price is not None:
            item.price = price
        if description is not None:
            item.description = description
        if is_available is not None:
            item.is_available = is_available

        try:
            session.commit()
            logging.info(f"Successfully updated Menu Item ID {item_id}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to update menu item: {e.orig}")


def delete_menu_item(item_id: int) -> None:
    with session_scope() as session:
        item = session.query(MenuItem).filter_by(id=item_id).first()
        if not item:
            logging.error(f"Menu Item with ID {item_id} does not exist.")
            return
        session.delete(item)
        try:
            session.commit()
            logging.info(f"Successfully deleted Menu Item ID {item_id}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to delete menu item: {e.orig}")


def list_menu_items(
    category: Optional[str] = None,
    is_available: Optional[bool] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
) -> None:
    with session_scope() as session:
        query = session.query(MenuItem)
        if category:
            query = query.filter_by(category=category)
        if is_available is not None:
            query = query.filter_by(is_available=is_available)
        if price_min is not None:
            query = query.filter(MenuItem.price >= price_min)
        if price_max is not None:
            query = query.filter(MenuItem.price <= price_max)

        menu_items = query.all()
        if not menu_items:
            logging.info("No menu items found matching the criteria.")
        else:
            for item in menu_items:
                availability = "Available" if item.is_available else "Unavailable"
                logging.info(
                    f"Menu Item ID: {item.id}, Name: {item.name}, Category: {item.category}, "
                    f"Price: ${item.price:.2f}, Availability: {availability}, Description: {item.description}"
                )
