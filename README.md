# Gestion d'un restaurant

Application en GUI pour gérer un restaurant.

## Structure

```bash
restaurant-manager/
├── venv/
├── data/
│   └── restaurant.db
├── src/
│   ├── controllers/
│   │   ├── __pycache__/
│   │   ├── base_controller.py
│   │   └── table_controller.py
│   ├── gui/
│   │   ├── __pycache__/
│   │   ├── tab_components/
│   │   │   └── table_card.py
│   │   ├── dialogs/
│   │   │   ├── __pycache__/
│   │   │   ├── message_dialog.py
│   │   │   └── table_dialog.py
│   │   └── views/
│   │       ├── __pycache__/
│   │       ├── customers_view.py
│   │       ├── menu_view.py
│   │       ├── orders_view.py
│   │       ├── reservations_view.py
│   │       ├── tables_view.py
│   │       └── main_window.py
│   ├── models/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── customer.py
│   │   ├── menu_item.py
│   │   ├── order_item.py
│   │   ├── order.py
│   │   ├── reservation.py
│   │   └── table.py
│   ├── services/
│   │   ├── __pycache__/
│   │   ├── base.py
│   │   ├── service_manager.py
│   │   └── table_service.py
│   │
│   └── utils/
│       ├── __pycache__/
│       ├── colors.py
│       ├── database.py
│       └── logger.py
├── tests/
├── .gitignore
├── Dockerfile
├── main.py
├── README.md
├── requirements.txt
└── restaurant_manager.log
```

## Utilisation

Exécutez le script `main.py`
