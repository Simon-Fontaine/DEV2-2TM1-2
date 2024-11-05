import logging
from argparse import Namespace

from models.restaurant import Restaurant
from models.customer import Customer


def add_customer(args: Namespace, restaurant: Restaurant) -> None:
    new_customer = Customer(args.customer_id, args.name, args.contact_info)
    restaurant.add_customer(new_customer)
    logging.info(f"Added customer: {args.name} (ID: {args.customer_id})")


def remove_customer(args: Namespace, restaurant: Restaurant) -> None:
    restaurant.remove_customer(args.customer_id)
    logging.info(f"Removed customer with ID: {args.customer_id}")


def update_customer(args: Namespace, restaurant: Restaurant) -> None:

    updates = {}
    if args.name:
        updates["name"] = args.name
    if args.contact_info:
        updates["contact_info"] = args.contact_info

    restaurant.update_customer(args.customer_id, **updates)
    logging.info(f"Updated customer with ID: {args.customer_id}")


def list_customers(args: Namespace, restaurant: Restaurant) -> None:
    customers = restaurant.list_customers()

    if not customers:
        logging.info("No customers found matching the criteria.")
    else:
        for customer in customers:
            logging.info(f"\n{customer}\n")
