import logging
from argparse import Namespace

from models.restaurant import Restaurant
from models.staff import Staff


def add_staff(args: Namespace, restaurant: Restaurant) -> None:
    staff = Staff(args.staff_id, args.name, args.role, args.assigned_tables)
    restaurant.add_staff(staff)
    logging.info(f"Added staff member: {args.name} (ID: {args.staff_id})")


def remove_staff(args: Namespace, restaurant: Restaurant) -> None:
    restaurant.remove_staff(args.staff_id)
    logging.info(f"Removed staff member with ID: {args.staff_id}")


def update_staff(args: Namespace, restaurant: Restaurant) -> None:

    updates = {}
    if args.name:
        updates["name"] = args.name
    if args.role:
        updates["role"] = args.role
    if args.assigned_tables:
        updates["assigned_tables"] = args.assigned_tables

    restaurant.update_staff(args.staff_id, **updates)
    logging.info(f"Updated staff member with ID: {args.staff_id}")


def list_staff(args: Namespace, restaurant: Restaurant) -> None:
    staffs = restaurant.list_staff()

    if args.role:
        staffs = [staff for staff in staffs if staff.role == args.role]

    if not staffs:
        logging.info("No staff members found matching the criteria.")
    else:
        for staff in staffs:
            logging.info(f"\n{staff}\n")
