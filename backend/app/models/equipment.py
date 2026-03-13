import uuid
from datetime import datetime

from sqlmodel import Field, Relationship

from app.domain.equipment import EquipmentBase
from app.domain.utils import get_datetime_utc


class Equipment(EquipmentBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_id: uuid.UUID = Field(foreign_key="customer.id", ondelete="CASCADE")
    created_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    customer: "Customer" = Relationship(back_populates="equipment")  # noqa: F821
    service_requests: list["ServiceRequest"] = Relationship(  # noqa: F821
        back_populates="equipment"
    )
