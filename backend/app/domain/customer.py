import uuid
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class CustomerBase(SQLModel):
    name: str = Field(max_length=255)
    company_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    address: str | None = None
    tax_id: str | None = Field(default=None, max_length=50)
    segment: str = Field(default="walk_in")  # enterprise, smb, walk_in
    notes: str | None = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(SQLModel):
    name: str | None = None
    company_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    tax_id: str | None = None
    segment: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class CustomerPublic(CustomerBase):
    id: uuid.UUID
    created_at: datetime | None
    updated_at: datetime | None


class CustomersPublic(SQLModel):
    data: list[CustomerPublic]
    count: int
