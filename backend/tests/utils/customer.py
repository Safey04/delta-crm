from sqlmodel import Session

from app.domain.customer import CustomerCreate
from app.models.customer import Customer
from app.repository import customer as customer_repo
from tests.utils.utils import random_lower_string


def create_random_customer(db: Session, **overrides) -> Customer:
    defaults = {
        "name": f"Customer {random_lower_string()[:8]}",
        "company_name": f"Company {random_lower_string()[:6]}",
        "phone": "+20123456789",
        "email": f"{random_lower_string()[:8]}@example.com",
        "segment": "smb",
    }
    defaults.update(overrides)
    return customer_repo.create_customer(
        session=db, customer_in=CustomerCreate(**defaults)
    )
