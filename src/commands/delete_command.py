from models.table import Table


def delete_table(args):
    table_number = args.id

    table_to_delete = Table.load_table(table_number)
    if not table_to_delete:
        print(f"Error: Table {table_number} not found.")
        return

    if table_to_delete.delete():
        print(f"Success: Table {table_number} deleted successfully.")
    else:
        print(f"Error: Failed to delete Table {table_number}.")
