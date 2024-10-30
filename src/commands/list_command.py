from models.table import Table


def list_tables(args):
    tables = Table.list_tables()
    if not tables:
        print("No tables available.")
        return

    print("Current tables in the system:")
    for table in tables:
        print(
            f"Table {table.table_number} - Capacity: {table.capacity} - Status: {table.status}"
        )
