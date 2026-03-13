import uuid
from datetime import datetime

from sqlmodel import Field, Relationship

from app.domain.service_visit import ServiceVisitBase
from app.domain.utils import get_datetime_utc


class ServiceVisit(ServiceVisitBase, table=True):
    __tablename__ = "service_visit"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    service_request_id: uuid.UUID = Field(
        foreign_key="service_request.id", ondelete="CASCADE"
    )
    engineer_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    created_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    service_request: "ServiceRequest" = Relationship(back_populates="service_visits")  # noqa: F821
