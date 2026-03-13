import uuid
from datetime import datetime

from sqlmodel import Field, Relationship

from app.domain.contact import ContactBase
from app.domain.utils import get_datetime_utc


class Contact(ContactBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    customer_id: uuid.UUID = Field(foreign_key="customer.id", ondelete="CASCADE")
    created_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    customer: "Customer" = Relationship(back_populates="contacts")  # noqa: F821
