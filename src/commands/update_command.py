from models.table import Table, TableStatus


def update_table(args):
    table_number = args.id
    new_status_input = args.status.strip() if args.status else None
    new_capacity = args.capacity

    if new_status_input is None and new_capacity is None:
        print("No updates were specified. Please provide a new status or capacity.")
        return

    table_to_update = Table.load_table(table_number)
    if not table_to_update:
        print(f"Error: Table {table_number} not found.")
        return

    if new_status_input:
        try:
            new_status = TableStatus[new_status_input.upper().replace(" ", "_")]
            if table_to_update.update_status(new_status):
                print(
                    f"Success: Table {table_number} status updated to '{new_status}'."
                )
            else:
                print(f"Error: Failed to update status for Table {table_number}.")
        except KeyError:
            print(
                f"Error: Invalid status '{new_status_input}'. Valid statuses are: {[status.value for status in TableStatus]}"
            )
            return

    if new_capacity is not None:
        try:
            if table_to_update.update_capacity(new_capacity):
                print(
                    f"Success: Table {table_number} capacity updated to {new_capacity}."
                )
        except ValueError as e:
            print(f"Error: {e}")
