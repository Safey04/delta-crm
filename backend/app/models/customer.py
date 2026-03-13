import uuid
from datetime import datetime

from sqlmodel import Field, Relationship

from app.domain.customer import CustomerBase
from app.domain.utils import get_datetime_utc


class Customer(CustomerBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    updated_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships (forward refs resolved when Contact, Equipment, ServiceRequest are created)
    contacts: list["Contact"] = Relationship(  # noqa: F821
        back_populates="customer", cascade_delete=True
    )
    equipment: list["Equipment"] = Relationship(  # noqa: F821
        back_populates="customer", cascade_delete=True
    )
    service_requests: list["ServiceRequest"] = Relationship(  # noqa: F821
        back_populates="customer"
    )
