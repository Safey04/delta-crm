import uuid
from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel

from app.domain.user import UserBase
from app.domain.utils import get_datetime_utc


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    supabase_auth_id: uuid.UUID = Field(unique=True, index=True)
    hashed_password: str = Field(default="")  # Keep for backward compat during migration, unused with Supabase
    role_id: uuid.UUID | None = Field(default=None, foreign_key="role.id", ondelete="SET NULL")
    created_at: datetime | None = Field(default_factory=get_datetime_utc)
    updated_at: datetime | None = Field(default_factory=get_datetime_utc)

    # Relationships
    role: "Role" = Relationship(back_populates="users")  # nullable via FK
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
