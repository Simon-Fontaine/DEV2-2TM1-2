# Gestion des Tables de Restaurant (MVP)

Application en ligne de commande pour gérer un restaurant.

## Structure

```bash
project_root/
├── src/
│   ├── main.py
│   ├── commands/
│   │   ├── add_command.py
│   │   ├── delete_command.py
│   │   ├── list_command.py
│   │   └── update_command.py
│   ├── models/
│   │   ├── customer.py
│   │   ├── order.py
│   │   ├── reservation.py
│   │   ├── staff.py
│   │   └── table.py
├── Dockerfile
├── README.md
├── requirements.txt
└── restaurant_state.json
```

## Utilisation

Exécutez le script `main.py` avec les commandes suivantes :

- **Ajouter une table :**

```bash
python main.py table add <table_number> <capacity> [--status <status>]
```

- **Ajouter une reservation :**

```bash
python main.py reservation add <reservation_id> <customer_id> <table_number> <number_of_people> <reservation_time>
```

- **Ajouter une commande :**

```bash
python main.py order add <order_id> <table_number> <items: List[dish_name:quantity:price]>
```

- **Ajouter un client**

```bash
python main.py customer add <customer_id> <name> <contact_info>
```

- **Ajouter un membre du personnel**

```bash
python main.py staff add <staff_id> <name> <role> [--assigned_tables <assigned_tables: List[int]>]
```

## Notes

- `restaurant_state.json` stocke l'état des tables et est créé automatiquement.
- Exécutez `main.py` depuis le répertoire `src/`.
