import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.role import (
    PermissionsPublic,
    RoleCreate,
    RolePermissionSet,
    RolePublic,
    RolesPublic,
    RoleUpdate,
    RoleWithPermissions,
)
from app.repository import role as role_repo

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=RolesPublic)
def read_roles(
    session: SessionDep,
    current_user: CurrentUser,  # noqa: ARG001 — enforces authentication
    skip: int = 0,
    limit: int = 100,
):
    roles = role_repo.get_roles(session=session, skip=skip, limit=limit)
    count = role_repo.get_roles_count(session=session)
    return RolesPublic(data=[RolePublic.model_validate(r) for r in roles], count=count)


@router.post("/", response_model=RolePublic)
def create_role(
    session: SessionDep,
    role_in: RoleCreate,
    _: CurrentUser = Depends(require_permission("user", "create")),
):
    existing = role_repo.get_role_by_name(session=session, name=role_in.name)
    if existing:
        raise HTTPException(status_code=409, detail="Role with this name already exists")
    role = role_repo.create_role(session=session, role_in=role_in)
    return RolePublic.model_validate(role)


@router.get("/permissions", response_model=PermissionsPublic)
def read_permissions(
    session: SessionDep,
    current_user: CurrentUser,  # noqa: ARG001 — enforces authentication
):
    perms = role_repo.get_permissions(session=session)
    return PermissionsPublic(
        data=list(perms),
        count=len(perms),
    )


@router.get("/{role_id}", response_model=RoleWithPermissions)
def read_role(
    role_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,  # noqa: ARG001 — enforces authentication
):
    role = role_repo.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    permissions = role_repo.get_role_permissions(session=session, role_id=role_id)
    return RoleWithPermissions(
        **RolePublic.model_validate(role).model_dump(),
        permissions=permissions,
    )


@router.patch("/{role_id}", response_model=RolePublic)
def update_role(
    role_id: uuid.UUID,
    session: SessionDep,
    role_in: RoleUpdate,
    _: CurrentUser = Depends(require_permission("user", "edit")),
):
    role = role_repo.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role = role_repo.update_role(session=session, db_role=role, role_in=role_in)
    return RolePublic.model_validate(role)


@router.put("/{role_id}/permissions", response_model=RoleWithPermissions)
def set_role_permissions(
    role_id: uuid.UUID,
    session: SessionDep,
    perm_set: RolePermissionSet,
    _: CurrentUser = Depends(require_permission("user", "edit")),
):
    role = role_repo.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    role_repo.set_role_permissions(
        session=session, role_id=role_id, permission_ids=perm_set.permission_ids,
    )
    permissions = role_repo.get_role_permissions(session=session, role_id=role_id)
    return RoleWithPermissions(
        **RolePublic.model_validate(role).model_dump(),
        permissions=permissions,
    )


@router.delete("/{role_id}")
def delete_role(
    role_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("user", "delete")),
):
    role = role_repo.get_role_by_id(session=session, role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    role_repo.delete_role(session=session, db_role=role)
    return {"message": "Role deleted"}
