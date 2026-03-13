import uuid

from sqlmodel import Session, select

from app.domain.role import RoleCreate, RoleUpdate
from app.models.role import Permission, Role, RolePermission


def create_role(*, session: Session, role_in: RoleCreate, is_system: bool = False) -> Role:
    db_role = Role.model_validate(role_in, update={"is_system": is_system})
    session.add(db_role)
    session.commit()
    session.refresh(db_role)
    return db_role


def get_role_by_name(*, session: Session, name: str) -> Role | None:
    return session.exec(select(Role).where(Role.name == name)).first()


def get_role_by_id(*, session: Session, role_id: uuid.UUID) -> Role | None:
    return session.get(Role, role_id)


def get_roles(*, session: Session, skip: int = 0, limit: int = 100) -> list[Role]:
    return list(session.exec(select(Role).offset(skip).limit(limit)).all())


def get_roles_count(*, session: Session) -> int:
    from sqlmodel import func
    return session.exec(select(func.count()).select_from(Role)).one()


def update_role(*, session: Session, db_role: Role, role_in: RoleUpdate) -> Role:
    role_data = role_in.model_dump(exclude_unset=True)
    db_role.sqlmodel_update(role_data)
    session.add(db_role)
    session.commit()
    session.refresh(db_role)
    return db_role


def delete_role(*, session: Session, db_role: Role) -> None:
    session.delete(db_role)
    session.commit()


# --- Permissions ---

def get_or_create_permission(
    *, session: Session, resource: str, action: str, description: str | None = None
) -> Permission:
    perm = session.exec(
        select(Permission).where(
            Permission.resource == resource,
            Permission.action == action,
        )
    ).first()
    if perm:
        return perm
    perm = Permission(resource=resource, action=action, description=description)
    session.add(perm)
    session.commit()
    session.refresh(perm)
    return perm


def get_permissions(*, session: Session) -> list[Permission]:
    return list(session.exec(select(Permission)).all())


def set_role_permissions(
    *, session: Session, role_id: uuid.UUID, permission_ids: list[uuid.UUID]
) -> None:
    # Remove existing
    existing = session.exec(
        select(RolePermission).where(RolePermission.role_id == role_id)
    ).all()
    for rp in existing:
        session.delete(rp)

    # Add new
    for perm_id in permission_ids:
        session.add(RolePermission(role_id=role_id, permission_id=perm_id))

    session.commit()


def get_role_permissions(*, session: Session, role_id: uuid.UUID) -> list[Permission]:
    return list(
        session.exec(
            select(Permission)
            .join(RolePermission)
            .where(RolePermission.role_id == role_id)
        ).all()
    )
