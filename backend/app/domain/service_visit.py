import uuid
from datetime import date, datetime, time

from sqlmodel import SQLModel


class ServiceVisitBase(SQLModel):
    visit_date: date
    arrival_time: time | None = None
    departure_time: time | None = None
    notes: str | None = None


class ServiceVisitCreate(ServiceVisitBase):
    service_request_id: uuid.UUID


class ServiceVisitUpdate(SQLModel):
    visit_date: date | None = None
    arrival_time: time | None = None
    departure_time: time | None = None
    notes: str | None = None


class ServiceVisitPublic(ServiceVisitBase):
    id: uuid.UUID
    service_request_id: uuid.UUID
    engineer_id: uuid.UUID
    created_at: datetime | None


class ServiceVisitsPublic(SQLModel):
    data: list[ServiceVisitPublic]
    count: int
