import uuid

from sqlmodel import Field

from app.domain.sla_config import SLAConfigBase


class SLAConfig(SLAConfigBase, table=True):
    __tablename__ = "sla_config"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
