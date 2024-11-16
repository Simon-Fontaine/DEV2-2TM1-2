import logging
from sqlalchemy.orm import Session
from ..models.base import init_db, engine
from ..models.table import Table, TableStatus
from ..models.menu_item import MenuItem, MenuItemCategory

logger = logging.getLogger(__name__)


def initialize_database():
    """Initialize the database and create sample data if needed"""
    try:
        init_db()

        with Session(engine) as session:
            if session.query(Table).count() == 0:
                create_sample_data(session)

        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise


def create_sample_data(session: Session):
    """Create sample data for testing"""
    try:
        # Create sample tables
        tables = [
            Table(
                number=1,
                capacity=4,
                status=TableStatus.AVAILABLE,
                location="Main Floor",
            ),
            Table(
                number=2, capacity=2, status=TableStatus.AVAILABLE, location="Window"
            ),
            Table(
                number=3, capacity=6, status=TableStatus.AVAILABLE, location="Terrace"
            ),
        ]
        session.add_all(tables)

        # Create sample menu items
        menu_items = [
            MenuItem(
                name="Caesar Salad",
                category=MenuItemCategory.APPETIZER,
                price=8.99,
                description="Fresh romaine lettuce with classic Caesar dressing",
                preparation_time=10,
            ),
            MenuItem(
                name="Margherita Pizza",
                category=MenuItemCategory.MAIN_COURSE,
                price=14.99,
                description="Fresh tomatoes, mozzarella, and basil",
                preparation_time=20,
            ),
            MenuItem(
                name="Chocolate Cake",
                category=MenuItemCategory.DESSERT,
                price=6.99,
                description="Rich chocolate layer cake",
                preparation_time=5,
            ),
        ]
        session.add_all(menu_items)

        session.commit()
        logger.info("Sample data created successfully")

    except Exception as e:
        session.rollback()
        logger.error(f"Error creating sample data: {e}")
        raise
