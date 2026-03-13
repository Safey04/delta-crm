import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class ServiceRequestBase(SQLModel):
    description: str
    priority: str = Field(default="medium")  # low, medium, high, critical
    source: str = Field(default="phone")  # phone, email, walk_in


class ServiceRequestCreate(ServiceRequestBase):
    customer_id: uuid.UUID
    equipment_id: uuid.UUID | None = None


class ServiceRequestUpdate(SQLModel):
    description: str | None = None
    priority: str | None = None
    diagnosis: str | None = None
    resolution_notes: str | None = None
    assigned_engineer_id: uuid.UUID | None = None
    status: str | None = None


class ServiceRequestPublic(ServiceRequestBase):
    id: uuid.UUID
    customer_id: uuid.UUID
    equipment_id: uuid.UUID | None
    assigned_engineer_id: uuid.UUID | None
    status: str
    diagnosis: str | None
    resolution_notes: str | None
    sla_response_due: datetime | None
    sla_resolution_due: datetime | None
    sla_response_breached: bool
    sla_resolution_breached: bool
    created_by: uuid.UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class ServiceRequestsPublic(SQLModel):
    data: list[ServiceRequestPublic]
    count: int


class ServiceRequestStatusUpdate(SQLModel):
    """Dedicated schema for status transitions."""

    status: str
    notes: str | None = None
