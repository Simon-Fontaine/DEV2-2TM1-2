# Gestion d'un restaurant

Application en GUI pour gérer un restaurant.

## Structure

```bash
restaurant-manager/
├── venv/
├── data/
│   └── restaurant.db
├── src/
│   ├── gui/
│   │   ├── tab_components/
│   │   │   ├── grid_cell.py
│   │   │   ├── menu_card.py
│   │   │   ├── menu_category_frame.py
│   │   │   ├── order_card.py
│   │   │   └── table_card.py
│   │   ├── dialogs/
│   │   │   ├── add_items_dialog.py
│   │   │   ├── customer_dialog.py
│   │   │   ├── menu_item_dialog.py
│   │   │   ├── message_dialog.py
│   │   │   ├── new_order_dialog.py
│   │   │   ├── payment_dialog.py
│   │   │   └── table_dialog.py
│   │   ├── views/
│   │   │   ├── base_view.py
│   │   │   ├── customers_view.py
│   │   │   ├── menu_view.py
│   │   │   ├── orders_view.py
│   │   │   ├── reservations_view.py
│   │   │   └── tables_view.py
│   │   └── main_window.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base_models.py
│   │   ├── customer.py
│   │   ├── menu_item.py
│   │   ├── order_item.py
│   │   ├── order.py
│   │   ├── reservation.py
│   │   └── table.py
│   ├── services/
│   │   ├── base_service.py
│   │   ├── customer_service.py
│   │   ├── menu_item_service.py
│   │   ├── order_service.py
│   │   └── table_service.py
│   └── utils/
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
