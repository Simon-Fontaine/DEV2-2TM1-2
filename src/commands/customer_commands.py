import logging
from typing import Optional
from models.db import session_scope
from models.customer import Customer
from sqlalchemy.exc import IntegrityError


def add_customer(name: str, contact_info: str) -> None:
    with session_scope() as session:
        new_customer = Customer(name=name, contact_info=contact_info)
        session.add(new_customer)
        try:
            session.commit()
            logging.info(f"Successfully added Customer '{name}'.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to add customer: {e.orig}")


def update_customer(
    customer_id: int,
    name: Optional[str] = None,
    contact_info: Optional[str] = None,
) -> None:
    with session_scope() as session:
        customer = session.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            logging.error(f"Customer with ID {customer_id} does not exist.")
            return

        if name is not None:
            customer.name = name
        if contact_info is not None:
            customer.contact_info = contact_info

        try:
            session.commit()
            logging.info(f"Successfully updated Customer ID {customer.id}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to update customer: {e.orig}")


def delete_customer(customer_id: int) -> None:
    with session_scope() as session:
        customer = session.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            logging.error(f"Customer with ID {customer_id} does not exist.")
            return
        session.delete(customer)
        try:
            session.commit()
            logging.info(f"Successfully deleted Customer ID {customer_id}.")
        except IntegrityError as e:
            session.rollback()
            logging.error(f"Failed to delete customer: {e.orig}")


def list_customers() -> None:
    with session_scope() as session:
        customers = session.query(Customer).all()
        if not customers:
            logging.info("No customers found.")
        else:
            for customer in customers:
                logging.info(
                    f"Customer ID: {customer.id}, Name: {customer.name}, Contact Info: {customer.contact_info}"
                )
