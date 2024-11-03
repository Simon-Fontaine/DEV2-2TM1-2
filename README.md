# Gestion des Tables de Restaurant (MVP)

Application en ligne de commande pour gérer les tables d'un restaurant : ajout, suppression, mise à jour et listing des tables avec statut et capacité.

## Structure

```bash
project_root/
├── src/
│   ├── main.py
│   ├── models/
│   │   ├── table.py
│   │   └── restaurant.py
│   ├── utils/
│   │   └── serialization.py  
└── restaurant_state.json
```

## Utilisation

Exécutez le script `main.py` avec les commandes suivantes :

- **Ajouter une table :**

```bash
python main.py add <table_number> --capacity <capacity> [--status <status>]
```


- **Supprimer une table :**

```bash
python main.py delete <table_number>
```

- **Mettre à jour une table :**

```bash
python main.py update <table_number> [--capacity <new_capacity>] [--status <new_status>]
```

- **Lister les tables :**

```bash
python main.py list
```

## Notes

- `restaurant_state.json` stocke l'état des tables et est créé automatiquement.
- Exécutez `main.py` depuis le répertoire `src/`.
