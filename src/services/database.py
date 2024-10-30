import sqlite3
from contextlib import contextmanager


class Database:
    def __init__(self, db_name="restaurant.db"):
        self.db_name = db_name
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the database schema if it doesn't already exist."""
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tables (
                    table_number INTEGER PRIMARY KEY,
                    capacity INTEGER NOT NULL,
                    status TEXT NOT NULL
                )
            """
            )

    @contextmanager
    def get_connection(self):
        """Provide a database connection within a context."""
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()
