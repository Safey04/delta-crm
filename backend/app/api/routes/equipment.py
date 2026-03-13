import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.equipment import (
    EquipmentCreate,
    EquipmentListPublic,
    EquipmentPublic,
    EquipmentUpdate,
    EquipmentWithCustomer,
)
from app.repository import customer as customer_repo
from app.repository import equipment as equipment_repo

router = APIRouter(tags=["equipment"])


# --- Global equipment routes ---


@router.get("/equipment", response_model=EquipmentListPublic)
def read_all_equipment(
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
):
    items = equipment_repo.get_all_equipment(
        session=session, skip=skip, limit=limit, search=search
    )
    count = equipment_repo.get_all_equipment_count(session=session, search=search)
    data = []
    for e in items:
        pub = EquipmentWithCustomer.model_validate(e)
        pub.customer_name = e.customer.name if e.customer else None
        data.append(pub)
    return EquipmentListPublic(data=data, count=count)


@router.get("/equipment/{equipment_id}", response_model=EquipmentWithCustomer)
def read_equipment(
    equipment_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
):
    eq = equipment_repo.get_equipment_by_id(
        session=session, equipment_id=equipment_id
    )
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    pub = EquipmentWithCustomer.model_validate(eq)
    pub.customer_name = eq.customer.name if eq.customer else None
    return pub


# --- Customer-scoped equipment routes ---


@router.get("/customers/{customer_id}/equipment", response_model=EquipmentListPublic)
def read_customer_equipment(
    customer_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "view")),
):
    customer = customer_repo.get_customer_by_id(
        session=session, customer_id=customer_id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    items = equipment_repo.get_equipment_by_customer(
        session=session, customer_id=customer_id
    )
    count = equipment_repo.get_equipment_count_by_customer(
        session=session, customer_id=customer_id
    )
    return EquipmentListPublic(
        data=[EquipmentPublic.model_validate(e) for e in items], count=count
    )


@router.post("/customers/{customer_id}/equipment", response_model=EquipmentPublic)
def create_equipment(
    customer_id: uuid.UUID,
    session: SessionDep,
    equipment_in: EquipmentCreate,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    if equipment_in.customer_id != customer_id:
        raise HTTPException(status_code=400, detail="Customer ID mismatch")
    customer = customer_repo.get_customer_by_id(
        session=session, customer_id=customer_id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    eq = equipment_repo.create_equipment(session=session, equipment_in=equipment_in)
    return EquipmentPublic.model_validate(eq)


@router.patch("/equipment/{equipment_id}", response_model=EquipmentPublic)
def update_equipment(
    equipment_id: uuid.UUID,
    session: SessionDep,
    equipment_in: EquipmentUpdate,
    _: CurrentUser = Depends(require_permission("customer", "edit")),
):
    eq = equipment_repo.get_equipment_by_id(
        session=session, equipment_id=equipment_id
    )
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    eq = equipment_repo.update_equipment(
        session=session, db_equipment=eq, equipment_in=equipment_in
    )
    return EquipmentPublic.model_validate(eq)


@router.delete("/equipment/{equipment_id}")
def delete_equipment(
    equipment_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("customer", "delete")),
):
    eq = equipment_repo.get_equipment_by_id(
        session=session, equipment_id=equipment_id
    )
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    equipment_repo.delete_equipment(session=session, db_equipment=eq)
    return {"message": "Equipment deleted"}
