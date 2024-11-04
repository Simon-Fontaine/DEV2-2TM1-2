import logging
from datetime import datetime
from models.restaurant import Restaurant
from models.reservation import Reservation, ReservationStatus


def add_reservation(args, restaurant: Restaurant) -> None:
    reservation_time = datetime.strptime(args.reservation_time, "%Y-%m-%d %H:%M")
    new_reservation = Reservation(
        args.reservation_id,
        args.customer_id,
        args.table_number,
        args.number_of_people,
        reservation_time,
    )
    restaurant.add_reservation(new_reservation)
    logging.info(
        f"Added reservation: #{new_reservation.id} for table {new_reservation.table_number} "
        f"(for {new_reservation.number_of_people} people on {reservation_time:%Y-%m-%d %H:%M})"
    )


def update_reservation(args, restaurant: Restaurant) -> None:
    reservation = restaurant.get_reservation(args.reservation_id)
    if not reservation:
        raise ValueError(f"Reservation not found: #{args.reservation_id}")

    updates = {}
    if args.table_number:
        updates["table_number"] = args.table_number
    if args.number_of_people:
        updates["number_of_people"] = args.number_of_people
    if args.status:
        updates["status"] = ReservationStatus(args.status)
    if args.reservation_time:
        updates["reservation_time"] = datetime.strptime(
            args.reservation_time, "%Y-%m-%d %H:%M"
        )

    restaurant.update_reservation(reservation.id, **updates)

    logging.info(
        f"Updated reservation: #{reservation.id} "
        f"(table: #{reservation.table_number}, people: {reservation.number_of_people}, "
        f"time: {reservation.reservation_time:%Y-%m-%d %H:%M}, status: {reservation.status.value})"
    )


def cancel_reservation(args, restaurant: Restaurant) -> None:
    reservation = restaurant.get_reservation(args.reservation_id)
    if not reservation:
        raise ValueError(f"Reservation not found: #{args.reservation_id}")

    restaurant.cancel_reservation(args.reservation_id)
    logging.info(f"Canceled reservation: #{args.reservation_id}")


def list_reservations(args, restaurant: Restaurant) -> None:
    reservations = restaurant.list_reservations()

    if not reservations:
        logging.info("No reservations found")
        return

    for reservation in reservations:
        logging.info(reservation)