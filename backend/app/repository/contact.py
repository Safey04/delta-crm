import uuid

from sqlmodel import Session, func, select

from app.domain.contact import ContactCreate, ContactUpdate
from app.models.contact import Contact


def create_contact(*, session: Session, contact_in: ContactCreate) -> Contact:
    db_contact = Contact.model_validate(contact_in)
    session.add(db_contact)
    session.commit()
    session.refresh(db_contact)
    return db_contact


def get_contact_by_id(*, session: Session, contact_id: uuid.UUID) -> Contact | None:
    return session.get(Contact, contact_id)


def get_contacts_by_customer(
    *, session: Session, customer_id: uuid.UUID
) -> list[Contact]:
    return list(
        session.exec(select(Contact).where(Contact.customer_id == customer_id)).all()
    )


def get_contacts_count_by_customer(*, session: Session, customer_id: uuid.UUID) -> int:
    return session.exec(
        select(func.count())
        .select_from(Contact)
        .where(Contact.customer_id == customer_id)
    ).one()


def update_contact(
    *, session: Session, db_contact: Contact, contact_in: ContactUpdate
) -> Contact:
    contact_data = contact_in.model_dump(exclude_unset=True)
    db_contact.sqlmodel_update(contact_data)
    session.add(db_contact)
    session.commit()
    session.refresh(db_contact)
    return db_contact


def delete_contact(*, session: Session, db_contact: Contact) -> None:
    session.delete(db_contact)
    session.commit()
