import logging
from sqlalchemy.orm import Session
from ..models.base_model import init_db, engine
from ..models.table import Table, TableStatus
from ..models.menu_item import MenuItem, MenuItemCategory
from ..models.customer import Customer

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
        # Create sample tables with different locations and capacities
        tables = [
            # Main Floor Tables (2x2 arrangement)
            Table(
                number=1,
                capacity=2,
                status=TableStatus.AVAILABLE,
                location="Main Floor",
                grid_x=1,  # Top row
                grid_y=1,
            ),
            Table(
                number=2,
                capacity=2,
                status=TableStatus.AVAILABLE,
                location="Main Floor",
                grid_x=2,
                grid_y=1,
            ),
            Table(
                number=3,
                capacity=4,
                status=TableStatus.OCCUPIED,
                location="Main Floor",
                grid_x=1,  # Bottom row
                grid_y=2,
            ),
            Table(
                number=4,
                capacity=4,
                status=TableStatus.AVAILABLE,
                location="Main Floor",
                grid_x=2,
                grid_y=2,
            ),
            # Window Tables (right side)
            Table(
                number=5,
                capacity=2,
                status=TableStatus.RESERVED,
                location="Window",
                grid_x=4,  # Right column
                grid_y=0,
            ),
            Table(
                number=6,
                capacity=4,
                status=TableStatus.AVAILABLE,
                location="Window",
                grid_x=4,
                grid_y=1,
            ),
            Table(
                number=7,
                capacity=6,
                status=TableStatus.AVAILABLE,
                location="Window",
                grid_x=4,
                grid_y=2,
            ),
            # Terrace Tables (bottom row)
            Table(
                number=8,
                capacity=4,
                status=TableStatus.AVAILABLE,
                location="Terrace",
                grid_x=1,
                grid_y=4,
            ),
            Table(
                number=9,
                capacity=6,
                status=TableStatus.CLEANING,
                location="Terrace",
                grid_x=2,
                grid_y=4,
            ),
            Table(
                number=10,
                capacity=8,
                status=TableStatus.AVAILABLE,
                location="Terrace",
                grid_x=3,
                grid_y=4,
            ),
            # Private Room Tables (top right)
            Table(
                number=11,
                capacity=8,
                status=TableStatus.AVAILABLE,
                location="Private Room",
                grid_x=5,  # Far right
                grid_y=0,
            ),
            Table(
                number=12,
                capacity=10,
                status=TableStatus.MAINTENANCE,
                location="Private Room",
                grid_x=5,
                grid_y=1,
            ),
        ]
        session.add_all(tables)

        # Create sample customers with valid phone numbers
        customers = [
            Customer(
                name="John Smith",
                phone="1234567890",  # Fixed phone number format
                email="john.smith@email.com",
                notes="Prefers window seating, regular customer",
            ),
            Customer(
                name="Emma Wilson",
                phone="2345678901",
                email="emma.w@email.com",
                notes="Allergic to shellfish",
            ),
            Customer(
                name="Michael Chen",
                phone="3456789012",
                email="m.chen@email.com",
                notes="VIP customer, prefers table 7",
            ),
            Customer(
                name="Sarah Johnson",
                phone="4567890123",
                email="sarah.j@email.com",
                notes="Birthday celebration on file",
            ),
            Customer(
                name="David Brown",
                phone="5678901234",
                email="d.brown@email.com",
                notes="Wine enthusiast, prefers terrace seating",
            ),
            Customer(
                name="Maria Garcia",
                phone="6789012345",
                email="m.garcia@email.com",
                notes="Vegetarian, regular weekend customer",
            ),
            Customer(
                name="James Wilson",
                phone="7890123456",
                email="j.wilson@email.com",
                notes="Corporate account",
            ),
            Customer(
                name="Lisa Anderson",
                phone="8901234567",
                email="l.anderson@email.com",
                notes="Gluten allergy",
            ),
            Customer(
                name="Robert Taylor",
                phone="9012345678",
                email="r.taylor@email.com",
                notes="Prefers quiet seating",
            ),
            Customer(
                name="Jennifer Lee",
                phone="0123456789",
                email="j.lee@email.com",
                notes="Regular lunch customer",
            ),
        ]
        session.add_all(customers)

        # Create sample menu items
        menu_items = [
            # Appetizers
            MenuItem(
                name="Classic Caesar Salad",
                category=MenuItemCategory.APPETIZER,
                price=9.99,
                description="Crisp romaine lettuce, homemade croutons, parmesan cheese, and our special Caesar dressing",
                preparation_time=10,
                allergens="Dairy, Eggs, Gluten",
            ),
            MenuItem(
                name="Bruschetta",
                category=MenuItemCategory.APPETIZER,
                price=7.99,
                description="Toasted baguette slices topped with fresh tomatoes, basil, and garlic",
                preparation_time=8,
                allergens="Gluten",
            ),
            MenuItem(
                name="Calamari Fritti",
                category=MenuItemCategory.APPETIZER,
                price=12.99,
                description="Crispy fried squid served with marinara sauce and lemon wedges",
                preparation_time=15,
                allergens="Gluten, Seafood",
            ),
            MenuItem(
                name="Spinach & Artichoke Dip",
                category=MenuItemCategory.APPETIZER,
                price=11.99,
                description="Creamy dip with spinach, artichokes, and melted cheese, served with tortilla chips",
                preparation_time=12,
                allergens="Dairy",
            ),
            # Main Courses
            MenuItem(
                name="Grilled Salmon",
                category=MenuItemCategory.MAIN_COURSE,
                price=24.99,
                description="Fresh Atlantic salmon fillet with herb butter, served with roasted vegetables",
                preparation_time=25,
                allergens="Fish",
            ),
            MenuItem(
                name="Beef Tenderloin",
                category=MenuItemCategory.MAIN_COURSE,
                price=32.99,
                description="8 oz beef tenderloin with red wine reduction, served with mashed potatoes",
                preparation_time=30,
                allergens="None",
            ),
            MenuItem(
                name="Mushroom Risotto",
                category=MenuItemCategory.MAIN_COURSE,
                price=18.99,
                description="Creamy Arborio rice with wild mushrooms and parmesan cheese",
                preparation_time=25,
                allergens="Dairy",
            ),
            MenuItem(
                name="Chicken Marsala",
                category=MenuItemCategory.MAIN_COURSE,
                price=21.99,
                description="Pan-seared chicken breast with Marsala wine sauce and mushrooms",
                preparation_time=25,
                allergens="Dairy",
            ),
            # Side Dishes
            MenuItem(
                name="Truffle Fries",
                category=MenuItemCategory.SIDE_DISH,
                price=6.99,
                description="Crispy fries tossed with truffle oil and parmesan",
                preparation_time=10,
                allergens="Dairy",
            ),
            MenuItem(
                name="Grilled Asparagus",
                category=MenuItemCategory.SIDE_DISH,
                price=5.99,
                description="Fresh asparagus grilled with olive oil and sea salt",
                preparation_time=8,
                allergens="None",
            ),
            MenuItem(
                name="Garlic Mashed Potatoes",
                category=MenuItemCategory.SIDE_DISH,
                price=5.99,
                description="Creamy mashed potatoes with roasted garlic",
                preparation_time=10,
                allergens="Dairy",
            ),
            # Desserts
            MenuItem(
                name="Tiramisu",
                category=MenuItemCategory.DESSERT,
                price=8.99,
                description="Classic Italian dessert with layers of coffee-soaked ladyfingers and mascarpone cream",
                preparation_time=15,
                allergens="Dairy, Eggs, Gluten",
            ),
            MenuItem(
                name="Chocolate Lava Cake",
                category=MenuItemCategory.DESSERT,
                price=9.99,
                description="Warm chocolate cake with a molten center, served with vanilla ice cream",
                preparation_time=20,
                allergens="Dairy, Eggs, Gluten",
            ),
            MenuItem(
                name="New York Cheesecake",
                category=MenuItemCategory.DESSERT,
                price=8.99,
                description="Classic creamy cheesecake with berry compote",
                preparation_time=15,
                allergens="Dairy, Eggs, Gluten",
            ),
            # Beverages
            MenuItem(
                name="Fresh Fruit Smoothie",
                category=MenuItemCategory.BEVERAGE,
                price=5.99,
                description="Blend of seasonal fruits with yogurt and honey",
                preparation_time=5,
                allergens="Dairy",
            ),
            MenuItem(
                name="Italian Coffee",
                category=MenuItemCategory.BEVERAGE,
                price=3.99,
                description="Freshly brewed espresso",
                preparation_time=3,
                allergens="None",
            ),
            MenuItem(
                name="Sparkling Water",
                category=MenuItemCategory.BEVERAGE,
                price=2.99,
                description="San Pellegrino sparkling mineral water",
                preparation_time=1,
                allergens="None",
            ),
            MenuItem(
                name="Craft Lemonade",
                category=MenuItemCategory.BEVERAGE,
                price=4.99,
                description="House-made lemonade with fresh mint",
                preparation_time=5,
                allergens="None",
            ),
            # Specials
            MenuItem(
                name="Chef's Special Pasta",
                category=MenuItemCategory.SPECIAL,
                price=26.99,
                description="Fresh homemade pasta with daily special sauce and ingredients",
                preparation_time=25,
                allergens="Gluten, Dairy",
            ),
            MenuItem(
                name="Catch of the Day",
                category=MenuItemCategory.SPECIAL,
                price=29.99,
                description="Fresh fish selection prepared according to chef's recommendation",
                preparation_time=30,
                allergens="Fish",
            ),
            MenuItem(
                name="Weekend Brunch Special",
                category=MenuItemCategory.SPECIAL,
                price=19.99,
                description="Chef's special brunch creation (Available weekends only)",
                preparation_time=20,
                allergens="Varies",
                is_available=False,
            ),
        ]
        session.add_all(menu_items)

        session.commit()
        logger.info("Sample data created successfully")

    except Exception as e:
        session.rollback()
        logger.error(f"Error creating sample data: {e}")
        raise
