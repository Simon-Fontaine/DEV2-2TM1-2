from enum import Enum
from datetime import datetime, timedelta
from typing import List, TYPE_CHECKING
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Table,
    Enum as SQLEnum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, mapped_column, Mapped, validates
from .base_model import BaseModel

if TYPE_CHECKING:
    from .customer import Customer
    from .table import Table


class ReservationStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CHECKED_IN = "Checked In"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    NO_SHOW = "No Show"


class ReservationPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


reservation_tables = Table(
    "reservation_tables",
    BaseModel.metadata,
    Column("reservation_id", Integer, ForeignKey("reservations.id")),
    Column("table_id", Integer, ForeignKey("tables.id")),
)


class Reservation(BaseModel):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    reservation_datetime: Mapped[datetime] = mapped_column(DateTime)
    duration: Mapped[int] = mapped_column(default=120)  # in minutes
    party_size: Mapped[int]
    status: Mapped[ReservationStatus] = mapped_column(
        SQLEnum(ReservationStatus), default=ReservationStatus.PENDING
    )
    priority: Mapped[ReservationPriority] = mapped_column(
        SQLEnum(ReservationPriority), default=ReservationPriority.MEDIUM
    )
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    special_requests: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    reminder_sent: Mapped[bool] = mapped_column(default=False)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="reservations")
    tables: Mapped[List["Table"]] = relationship(
        secondary=reservation_tables, back_populates="reservations"
    )

    @validates("party_size")
    def validate_party_size(self, key, value):
        """
        PRE: value est un entier
        POST: retourne value si il est compris entre 1 et 20 inclus
        RAISE:
            - TypeError: si value n'est pas un entier
            - ValueError: si value <= 0 ou value > 20
        """
        if not isinstance(value, int):
            raise TypeError("Party size must be an integer")
        if value <= 0:
            raise ValueError("Party size must be greater than 0")
        if value > 20:
            raise ValueError("Party size exceeds maximum capacity")
        return value

    @validates("duration")
    def validate_duration(self, key, value):
        """
        PRE: value est un entier positif représentant des minutes
        POST: retourne value si il est compris entre 30 et 480 minutes inclus
        RAISE: ValueError si hors limites
        """
        if value < 30:
            raise ValueError("Duration must be at least 30 minutes")
        if value > 480:
            raise ValueError("Duration cannot exceed 8 hours")
        return value

    @validates("reservation_datetime")
    def validate_reservation_datetime(self, key, value):
        """
        PRE: value est un objet datetime
        POST: retourne value si la date est dans le futur
        RAISE:
            - TypeError: si value n'est pas un datetime
            - ValueError: si la date est dans le passé
        """
        if not isinstance(value, datetime):
            raise TypeError("Reservation datetime must be a datetime object")
        if value < datetime.now():
            raise ValueError("Reservation time cannot be in the past")
        return value

    def is_late(self) -> bool:
        """
        PRE: la réservation a un statut et une date/heure définis
        POST: retourne True si :
              - le statut est CONFIRMED
              - l'heure actuelle dépasse de plus de 30 minutes l'heure de réservation
              retourne False dans tous les autres cas
        """
        if self.status != ReservationStatus.CONFIRMED:
            return False
        return datetime.now() > self.reservation_datetime + timedelta(minutes=30)

    def can_check_in(self) -> bool:
        """
        PRE: la réservation a un statut et une date/heure définis
        POST: retourne True si :
              - le statut est CONFIRMED
              - l'heure actuelle est entre 15 minutes avant et 30 minutes après l'heure de réservation
              retourne False dans tous les autres cas
        """
        now = datetime.now()
        check_in_window_start = self.reservation_datetime - timedelta(minutes=15)
        check_in_window_end = self.reservation_datetime + timedelta(minutes=30)
        return (
            self.status == ReservationStatus.CONFIRMED
            and check_in_window_start <= now <= check_in_window_end
        )

    def conflicts_with(self, other: "Reservation") -> bool:
        """
        PRE: other est une instance de Reservation
             les deux réservations ont des tables assignées
        POST: retourne True si :
              - les réservations partagent au moins une table
              - les périodes de réservation se chevauchent
              retourne False sinon
        RAISE:
            - TypeError: si other n'est pas une Reservation
            - ValueError: si les tables ne sont pas assignées
        """
        if not isinstance(other, Reservation):
            raise TypeError("Parameter must be a Reservation instance")

        if not self.tables or not other.tables:
            raise ValueError("Both reservations must have tables assigned")

        if not set(self.tables).intersection(set(other.tables)):
            return False

        self_end = self.get_end_time()
        other_end = other.get_end_time()

        return (
            self.reservation_datetime < other_end
            and other.reservation_datetime < self_end
        )

    def get_end_time(self) -> datetime:
        """
        PRE: la réservation a une date/heure et une durée définies
        POST: retourne un datetime représentant l'heure de fin de la réservation
              (heure de début + durée)
        """
        return self.reservation_datetime + timedelta(minutes=self.duration)

    def __repr__(self) -> str:
        return (
            f"<Reservation(id={self.id}, "
            f"customer={self.customer.name}, "
            f"datetime={self.reservation_datetime}, "
            f"status={self.status.value})>"
        )
