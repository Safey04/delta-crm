import uuid

from sqlmodel import Session, func, select

from app.domain.equipment import EquipmentCreate, EquipmentUpdate
from app.models.equipment import Equipment


def create_equipment(*, session: Session, equipment_in: EquipmentCreate) -> Equipment:
    db_equipment = Equipment.model_validate(equipment_in)
    session.add(db_equipment)
    session.commit()
    session.refresh(db_equipment)
    return db_equipment


def get_equipment_by_id(*, session: Session, equipment_id: uuid.UUID) -> Equipment | None:
    return session.get(Equipment, equipment_id)


def get_equipment_by_customer(
    *, session: Session, customer_id: uuid.UUID
) -> list[Equipment]:
    return list(
        session.exec(
            select(Equipment).where(Equipment.customer_id == customer_id)
        ).all()
    )


def get_equipment_count_by_customer(*, session: Session, customer_id: uuid.UUID) -> int:
    return session.exec(
        select(func.count()).select_from(Equipment).where(
            Equipment.customer_id == customer_id
        )
    ).one()


def get_all_equipment(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> list[Equipment]:
    query = select(Equipment)
    if search:
        query = query.where(
            Equipment.serial_number.ilike(f"%{search}%")  # type: ignore
            | Equipment.model.ilike(f"%{search}%")  # type: ignore
            | Equipment.manufacturer.ilike(f"%{search}%")  # type: ignore
        )
    return list(session.exec(query.offset(skip).limit(limit)).all())


def get_all_equipment_count(*, session: Session, search: str | None = None) -> int:
    query = select(func.count()).select_from(Equipment)
    if search:
        query = query.where(
            Equipment.serial_number.ilike(f"%{search}%")  # type: ignore
            | Equipment.model.ilike(f"%{search}%")  # type: ignore
        )
    return session.exec(query).one()


def update_equipment(
    *, session: Session, db_equipment: Equipment, equipment_in: EquipmentUpdate
) -> Equipment:
    equipment_data = equipment_in.model_dump(exclude_unset=True)
    db_equipment.sqlmodel_update(equipment_data)
    session.add(db_equipment)
    session.commit()
    session.refresh(db_equipment)
    return db_equipment


def delete_equipment(*, session: Session, db_equipment: Equipment) -> None:
    session.delete(db_equipment)
    session.commit()
