import uuid
from datetime import date, datetime

from sqlmodel import Field, SQLModel


class EquipmentBase(SQLModel):
    model: str = Field(max_length=255)
    serial_number: str = Field(max_length=255)
    manufacturer: str | None = Field(default=None, max_length=255)
    install_date: date | None = None
    warranty_expiry: date | None = None
    notes: str | None = None
    is_active: bool = True


class EquipmentCreate(EquipmentBase):
    customer_id: uuid.UUID


class EquipmentUpdate(SQLModel):
    model: str | None = None
    serial_number: str | None = None
    manufacturer: str | None = None
    install_date: date | None = None
    warranty_expiry: date | None = None
    notes: str | None = None
    is_active: bool | None = None


class EquipmentPublic(EquipmentBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    created_at: datetime | None


class EquipmentListPublic(SQLModel):
    data: list[EquipmentPublic]
    count: int


class EquipmentWithCustomer(EquipmentPublic):
    """For global equipment list — includes customer name."""
    customer_name: str | None = None
