from models.table import Table, TableStatus


def add_table(args):
    table_number = args.id
    capacity = args.capacity
    status_input = args.status.strip() if args.status else TableStatus.AVAILABLE.value

    try:
        status_enum = TableStatus[status_input.upper().replace(" ", "_")]
    except KeyError:
        print(
            f"Error: Invalid status '{status_input}'. Valid statuses are: {[status.value for status in TableStatus]}"
        )
        return

    new_table = Table.create(table_number, capacity, status_enum)
    if new_table:
        print(f"Success: Table {table_number} added successfully.")
    else:
        print(f"Error: Failed to add Table {table_number}. It may already exist.")
