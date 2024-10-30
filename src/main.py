import argparse
from commands.add_command import add_table
from commands.list_command import list_tables
from commands.update_command import update_table
from commands.delete_command import delete_table


def main():
    parser = argparse.ArgumentParser(description="Table Management System")
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # List tables
    parser_list = subparsers.add_parser("list", help="List all tables")
    parser_list.set_defaults(func=list_tables)

    # Update table status
    parser_update = subparsers.add_parser(
        "update", help="Update table status or capacity"
    )
    parser_update.add_argument("--id", type=int, required=True, help="Table ID")
    parser_update.add_argument("--status", type=str, help="New status")
    parser_update.add_argument("--capacity", type=int, help="New capacity")
    parser_update.set_defaults(func=update_table)

    # Add table
    parser_add = subparsers.add_parser("add", help="Add a new table")
    parser_add.add_argument("--id", type=int, required=True, help="Table ID")
    parser_add.add_argument(
        "--capacity", type=int, required=True, help="Table capacity"
    )
    parser_add.add_argument("--status", type=str, help="Table status")
    parser_add.set_defaults(func=add_table)

    # Delete table
    parser_delete = subparsers.add_parser("delete", help="Delete a table")
    parser_delete.add_argument("--id", type=int, required=True, help="Table ID")
    parser_delete.set_defaults(func=delete_table)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
