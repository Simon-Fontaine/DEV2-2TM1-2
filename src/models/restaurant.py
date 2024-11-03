import logging
import json
from typing import Dict, Optional
from models.table import Table, TableStatus
from utils.serialization import table_to_dict, table_from_dict


class Restaurant:
    def __init__(self) -> None:
        self.tables: Dict[int, Table] = {}

    def add_table(
        self,
        table_number: int,
        capacity: int,
        status: TableStatus = TableStatus.AVAILABLE,
    ) -> None:
        if table_number in self.tables:
            logging.error(f"La table {table_number} existe déjà.")
        else:
            try:
                table = Table(table_number, capacity, status)
                self.tables[table_number] = table
                logging.info(f"Table {table_number} ajoutée.")
            except ValueError as e:
                logging.error(e)

    def delete_table(self, table_number: int) -> None:
        if table_number in self.tables:
            del self.tables[table_number]
            logging.info(f"Table {table_number} supprimée.")
        else:
            logging.error(f"Table {table_number} introuvable.")

    def update_table(
        self,
        table_number: int,
        new_capacity: Optional[int] = None,
        new_status: Optional[str] = None,
    ) -> None:
        table = self.tables.get(table_number)
        if table:
            if new_capacity is not None:
                if new_capacity > 0:
                    table.capacity = new_capacity
                else:
                    logging.error("La capacité doit être un entier positif.")
                    return
            if new_status is not None:
                try:
                    table.update_status(TableStatus(new_status))
                except ValueError:
                    valid_statuses = [status.value for status in TableStatus]
                    logging.error(
                        f"Statut invalide: {new_status}. Doit être l'un de {valid_statuses}."
                    )
                    return
            logging.info(f"Table {table_number} mise à jour.")
        else:
            logging.error(f"Table {table_number} introuvable.")

    def list_tables(self) -> None:
        if not self.tables:
            logging.info("Aucune table disponible.")
        else:
            for table in self.tables.values():
                print(table)

    def save_state(self, filename: str) -> None:
        try:
            with open(filename, "w", encoding="utf-8") as file:
                data = [table_to_dict(table) for table in self.tables.values()]
                json.dump(data, file, ensure_ascii=False, indent=2)
            logging.debug(f"État du restaurant sauvegardé dans {filename}.")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde: {e}")

    @staticmethod
    def load_state(filename: str) -> "Restaurant":
        restaurant = Restaurant()
        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
                for table_data in data:
                    table = table_from_dict(table_data)
                    restaurant.tables[table.table_number] = table
            logging.debug(f"État du restaurant chargé depuis {filename}.")
        except FileNotFoundError:
            logging.warning(
                f"Fichier {filename} introuvable. Création d'un nouveau restaurant."
            )
        except Exception as e:
            logging.error(f"Erreur lors du chargement: {e}")
        return restaurant
