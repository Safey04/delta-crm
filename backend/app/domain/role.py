import uuid

from sqlmodel import Field, SQLModel


# Shared properties for Role
class RoleBase(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on role creation
class RoleCreate(RoleBase):
    pass


# Properties to receive on role update, all optional
class RoleUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


# Properties to return via API, id is always required
class RolePublic(RoleBase):
    id: uuid.UUID
    is_system: bool


class RolesPublic(SQLModel):
    data: list[RolePublic]
    count: int


# Shared properties for Permission
class PermissionBase(SQLModel):
    resource: str = Field(min_length=1, max_length=100)
    action: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


# Properties to return via API
class PermissionPublic(PermissionBase):
    id: uuid.UUID


class PermissionsPublic(SQLModel):
    data: list[PermissionPublic]
    count: int


# Schema for setting permissions on a role
class RolePermissionSet(SQLModel):
    permission_ids: list[uuid.UUID]


# Role with its associated permissions
class RoleWithPermissions(RolePublic):
    permissions: list[PermissionPublic] = []
