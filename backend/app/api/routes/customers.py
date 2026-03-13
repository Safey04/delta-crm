import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.customer import (
    CustomerCreate,
    CustomerPublic,
    CustomersPublic,
    CustomerUpdate,
)
from app.repository import customer as customer_repo

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=CustomersPublic)
def read_customers(
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
    skip: int = 0,
    limit: int = 100,
    segment: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
):
    customers = customer_repo.get_customers(
        session=session,
        skip=skip,
        limit=limit,
        segment=segment,
        is_active=is_active,
        search=search,
    )
    count = customer_repo.get_customers_count(
        session=session,
        segment=segment,
        is_active=is_active,
        search=search,
    )
    return CustomersPublic(
        data=[CustomerPublic.model_validate(c) for c in customers], count=count
    )


@router.post("/", response_model=CustomerPublic)
def create_customer(
    session: SessionDep,
    customer_in: CustomerCreate,
    _: CurrentUser = Depends(require_permission("customer", "create")),
):
    customer = customer_repo.create_customer(session=session, customer_in=customer_in)
    return CustomerPublic.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerPublic)
def read_customer(
    customer_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
):
    customer = customer_repo.get_customer_by_id(
        session=session, customer_id=customer_id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return CustomerPublic.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerPublic)
def update_customer(
    customer_id: uuid.UUID,
    session: SessionDep,
    customer_in: CustomerUpdate,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    customer = customer_repo.get_customer_by_id(
        session=session, customer_id=customer_id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer = customer_repo.update_customer(
        session=session, db_customer=customer, customer_in=customer_in
    )
    return CustomerPublic.model_validate(customer)


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "delete")),
):
    customer = customer_repo.get_customer_by_id(
        session=session, customer_id=customer_id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer_repo.delete_customer(session=session, db_customer=customer)
    return {"message": "Customer deleted"}
