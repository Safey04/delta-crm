import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from app.domain.role import RolePublic


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    full_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)


class UserCreate(SQLModel):
    """Manager creates a user — Supabase Auth account + local record."""
    email: EmailStr
    full_name: str | None = None
    phone: str | None = None
    password: str = Field(min_length=8, max_length=128)
    role_id: uuid.UUID


class UserUpdate(SQLModel):
    email: EmailStr | None = None
    full_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None
    role_id: uuid.UUID | None = None


class UserUpdateMe(SQLModel):
    full_name: str | None = None
    phone: str | None = None


class UserPublic(UserBase):
    id: uuid.UUID
    role_id: uuid.UUID | None
    role: RolePublic | None = None
    created_at: datetime | None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
