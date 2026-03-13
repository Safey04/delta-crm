import uuid

from sqlmodel import Session, func, select

from app.domain.customer import CustomerCreate, CustomerUpdate
from app.domain.utils import get_datetime_utc
from app.models.customer import Customer


def create_customer(*, session: Session, customer_in: CustomerCreate) -> Customer:
    db_customer = Customer.model_validate(customer_in)
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer


def get_customer_by_id(*, session: Session, customer_id: uuid.UUID) -> Customer | None:
    return session.get(Customer, customer_id)


def get_customers(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    segment: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> list[Customer]:
    query = select(Customer)
    if segment:
        query = query.where(Customer.segment == segment)
    if is_active is not None:
        query = query.where(Customer.is_active == is_active)
    if search:
        query = query.where(
            Customer.name.ilike(f"%{search}%")  # type: ignore
            | Customer.company_name.ilike(f"%{search}%")  # type: ignore
            | Customer.phone.ilike(f"%{search}%")  # type: ignore
            | Customer.email.ilike(f"%{search}%")  # type: ignore
        )
    return list(session.exec(query.offset(skip).limit(limit)).all())


def get_customers_count(
    *,
    session: Session,
    segment: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> int:
    query = select(func.count()).select_from(Customer)
    if segment:
        query = query.where(Customer.segment == segment)
    if is_active is not None:
        query = query.where(Customer.is_active == is_active)
    if search:
        query = query.where(
            Customer.name.ilike(f"%{search}%")  # type: ignore
            | Customer.company_name.ilike(f"%{search}%")  # type: ignore
        )
    return session.exec(query).one()


def update_customer(
    *, session: Session, db_customer: Customer, customer_in: CustomerUpdate
) -> Customer:
    customer_data = customer_in.model_dump(exclude_unset=True)
    db_customer.sqlmodel_update(customer_data)
    db_customer.updated_at = get_datetime_utc()
    session.add(db_customer)
    session.commit()
    session.refresh(db_customer)
    return db_customer


def delete_customer(*, session: Session, db_customer: Customer) -> None:
    session.delete(db_customer)
    session.commit()
