import uuid
from datetime import datetime

from sqlmodel import Field, Relationship

from app.domain.service_request import ServiceRequestBase
from app.domain.utils import get_datetime_utc


class ServiceRequest(ServiceRequestBase, table=True):
    __tablename__ = "service_request"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_id: uuid.UUID = Field(foreign_key="customer.id", ondelete="CASCADE")
    equipment_id: uuid.UUID | None = Field(
        default=None, foreign_key="equipment.id", ondelete="SET NULL"
    )
    assigned_engineer_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )
    created_by: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )

    status: str = Field(default="new")
    diagnosis: str | None = None
    resolution_notes: str | None = None

    # SLA fields
    sla_response_due: datetime | None = None
    sla_resolution_due: datetime | None = None
    sla_response_breached: bool = Field(default=False)
    sla_resolution_breached: bool = Field(default=False)
    sla_paused_at: datetime | None = None
    sla_total_paused_seconds: int = Field(default=0)

    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    updated_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    customer: "Customer" = Relationship(back_populates="service_requests")  # noqa: F821
    equipment: "Equipment | None" = Relationship(  # noqa: F821
        back_populates="service_requests"
    )
    service_visits: list["ServiceVisit"] = Relationship(  # noqa: F821
        back_populates="service_request", cascade_delete=True
    )
