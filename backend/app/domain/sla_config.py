import uuid

from sqlmodel import Field, SQLModel


class SLAConfigBase(SQLModel):
    segment: str = Field(unique=True)  # enterprise, smb, walk_in
    response_hours: int
    resolution_hours: int


class SLAConfigCreate(SLAConfigBase):
    pass


class SLAConfigUpdate(SQLModel):
    response_hours: int | None = None
    resolution_hours: int | None = None


class SLAConfigPublic(SLAConfigBase):
    id: uuid.UUID
