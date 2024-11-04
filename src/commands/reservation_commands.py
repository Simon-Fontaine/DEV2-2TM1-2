from commands.command import Command
from models.restaurant import Restaurant
from models.reservation import Reservation
from datetime import datetime
import logging


class AddReservationCommand(Command):

    def __init__(
        self,
        restaurant: Restaurant,
        reservation_id: int,
        customer_id: int,
        table_number: int,
        number_of_people: int,
        reservation_time_str: str,
    ):
        self.restaurant = restaurant
        self.reservation_id = reservation_id
        self.customer_id = customer_id
        self.table_number = table_number
        self.number_of_people = number_of_people
        self.reservation_time_str = reservation_time_str

    def execute(self) -> None:
        try:
            reservation_time = datetime.fromisoformat(self.reservation_time_str)
            reservation = Reservation(
                id=self.reservation_id,
                customer_id=self.customer_id,
                table_number=self.table_number,
                number_of_people=self.number_of_people,
                reservation_time=reservation_time,
                status_confirmed=True,
            )
            self.restaurant.add_reservation(reservation)
            logging.info(f"Reservation {self.reservation_id} added.")
        except ValueError as e:
            logging.error(f"Error adding reservation: {e}")


class CancelReservationCommand(Command):

    def __init__(self, restaurant: Restaurant, reservation_id: int):
        self.restaurant = restaurant
        self.reservation_id = reservation_id

    def execute(self) -> None:
        reservation = self.restaurant.reservations.get(self.reservation_id)
        if reservation:
            reservation.cancel()
            logging.info(f"Reservation {self.reservation_id} canceled.")
        else:
            logging.error(f"Reservation {self.reservation_id} not found.")


class ModifyReservationCommand(Command):

    def __init__(self, restaurant: Restaurant, reservation_id: int, **kwargs):
        self.restaurant = restaurant
        self.reservation_id = reservation_id
        self.updates = kwargs

    def execute(self) -> None:
        reservation = self.restaurant.reservations.get(self.reservation_id)
        if reservation:
            reservation.modify(**self.updates)
            logging.info(f"Reservation {self.reservation_id} modified.")
        else:
            logging.error(f"Reservation {self.reservation_id} not found.")


class ListReservationsCommand(Command):

    def __init__(self, restaurant: Restaurant):
        self.restaurant = restaurant

    def execute(self) -> None:
        reservations = self.restaurant.reservations.values()
        if reservations:
            for reservation in reservations:
                print(reservation)
        else:
            logging.info("No reservations found.")
