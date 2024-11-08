from sqlalchemy import Column, Integer, String, CheckConstraint
from sqlalchemy.orm import relationship, validates
from models.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    contact_info = Column(String(255), nullable=False)

    reservations = relationship(
        "Reservation", back_populates="customer", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("length(name) > 0", name="check_name_non_empty"),
        CheckConstraint(
            "length(contact_info) > 0", name="check_contact_info_non_empty"
        ),
    )

    @validates("name")
    def validate_name(self, key, value):
        if not value.strip():
            raise ValueError("Customer name cannot be empty.")
        return value

    @validates("contact_info")
    def validate_contact_info(self, key, value):
        if not value.strip():
            raise ValueError("Contact information cannot be empty.")
        return value

    def __repr__(self):
        return f"<Customer(id={self.id}, name={self.name}, contact_info={self.contact_info})>"
