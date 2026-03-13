import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class ContactBase(SQLModel):
    name: str = Field(max_length=255)
    title: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    is_primary: bool = False


class ContactCreate(ContactBase):
    customer_id: uuid.UUID


class ContactUpdate(SQLModel):
    name: str | None = None
    title: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    is_primary: bool | None = None


class ContactPublic(ContactBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime | None


class ContactsPublic(SQLModel):
    data: list[ContactPublic]
    count: int
