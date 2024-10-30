import sqlite3
from enum import Enum
from services.database import Database


class TableStatus(Enum):
    AVAILABLE = "Available"
    OCCUPIED = "Occupied"
    RESERVED = "Reserved"
    UNDER_MAINTENANCE = "Under Maintenance"

    def __str__(self):
        return self.value


class Table:
    db = Database()

    def __init__(
        self,
        table_number: int,
        capacity: int,
        status: TableStatus = TableStatus.AVAILABLE,
    ):
        self.table_number = table_number
        self.capacity = max(1, capacity)
        self.status = status

    @classmethod
    def create(
        cls,
        table_number: int,
        capacity: int,
        status: TableStatus = TableStatus.AVAILABLE,
    ):
        """Create a new table in the database and return an instance of Table if successful."""
        with cls.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO tables (table_number, capacity, status) VALUES (?, ?, ?)",
                    (table_number, capacity, status.value),
                )
                conn.commit()
                return cls(table_number, capacity, status)
            except sqlite3.IntegrityError:
                return None

    @classmethod
    def load_table(cls, table_number: int):
        """Load a table from the database by table_number and return an instance of Table if found."""
        with cls.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT table_number, capacity, status FROM tables WHERE table_number = ?",
                (table_number,),
            )
            row = cursor.fetchone()
            return cls(row[0], row[1], TableStatus(row[2])) if row else None

    @classmethod
    def list_tables(cls):
        """Fetch all tables from the database and return a list of Table instances."""
        with cls.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT table_number, capacity, status FROM tables")
            rows = cursor.fetchall()
            return [cls(row[0], row[1], TableStatus(row[2])) for row in rows]

    def delete(self):
        """Delete this table from the database. Returns True if successful, False otherwise."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM tables WHERE table_number = ?", (self.table_number,)
            )
            deleted = cursor.rowcount > 0
            if deleted:
                conn.commit()
            return deleted

    def update_status(self, new_status: TableStatus) -> bool:
        """Update the table status in the database and set it on the instance."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tables SET status = ? WHERE table_number = ?",
                (new_status.value, self.table_number),
            )
            if cursor.rowcount > 0:
                conn.commit()
                self.status = new_status
                return True
            return False

    def update_capacity(self, new_capacity: int) -> bool:
        """Update the table capacity in the database and set it on the instance."""
        if new_capacity < 1:
            raise ValueError("Capacity must be greater than 0.")
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tables SET capacity = ? WHERE table_number = ?",
                (new_capacity, self.table_number),
            )
            if cursor.rowcount > 0:
                conn.commit()
                self.capacity = new_capacity
                return True
            return False

    def __repr__(self):
        return f"Table(table_number={self.table_number}, capacity={self.capacity}, status={self.status})"
