import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.contact import (
    ContactCreate,
    ContactPublic,
    ContactsPublic,
    ContactUpdate,
)
from app.repository import contact as contact_repo
from app.repository import customer as customer_repo

router = APIRouter(prefix="/customers/{customer_id}/contacts", tags=["contacts"])


@router.get("/", response_model=ContactsPublic)
def read_contacts(
    customer_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
):
    customer = customer_repo.get_customer_by_id(
        session=session, customer_id=customer_id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    contacts = contact_repo.get_contacts_by_customer(
        session=session, customer_id=customer_id
    )
    count = contact_repo.get_contacts_count_by_customer(
        session=session, customer_id=customer_id
    )
    return ContactsPublic(
        data=[ContactPublic.model_validate(c) for c in contacts], count=count
    )


@router.post("/", response_model=ContactPublic)
def create_contact(
    customer_id: uuid.UUID,
    session: SessionDep,
    contact_in: ContactCreate,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    if contact_in.customer_id != customer_id:
        raise HTTPException(status_code=400, detail="Customer ID mismatch")
    customer = customer_repo.get_customer_by_id(
        session=session, customer_id=customer_id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    contact = contact_repo.create_contact(session=session, contact_in=contact_in)
    return ContactPublic.model_validate(contact)


@router.patch("/{contact_id}", response_model=ContactPublic)
def update_contact(
    customer_id: uuid.UUID,
    contact_id: uuid.UUID,
    session: SessionDep,
    contact_in: ContactUpdate,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    contact = contact_repo.get_contact_by_id(session=session, contact_id=contact_id)
    if not contact or contact.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact = contact_repo.update_contact(
        session=session, db_contact=contact, contact_in=contact_in
    )
    return ContactPublic.model_validate(contact)


@router.delete("/{contact_id}")
def delete_contact(
    customer_id: uuid.UUID,
    contact_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    contact = contact_repo.get_contact_by_id(session=session, contact_id=contact_id)
    if not contact or contact.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact_repo.delete_contact(session=session, db_contact=contact)
    return {"message": "Contact deleted"}
