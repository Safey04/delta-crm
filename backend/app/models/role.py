import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.domain.role import PermissionBase, RoleBase

if TYPE_CHECKING:
    from app.models.user import User


# Association table for many-to-many: Role <-> Permission
class RolePermission(SQLModel, table=True):
    role_id: uuid.UUID = Field(
        foreign_key="role.id", primary_key=True, ondelete="CASCADE"
    )
    permission_id: uuid.UUID = Field(
        foreign_key="permission.id", primary_key=True, ondelete="CASCADE"
    )


# Database model, database table inferred from class name
class Role(RoleBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    is_system: bool = Field(default=False)

    permissions: list["Permission"] = Relationship(
        back_populates="roles", link_model=RolePermission
    )
    users: list["User"] = Relationship(back_populates="role")


class Permission(PermissionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    roles: list[Role] = Relationship(
        back_populates="permissions", link_model=RolePermission
    )
