import uuid

from sqlmodel import Session

from app.domain.equipment import EquipmentCreate
from app.models.equipment import Equipment
from app.repository import equipment as equipment_repo
from tests.utils.utils import random_lower_string


def create_random_equipment(
    db: Session, customer_id: uuid.UUID, **overrides
) -> Equipment:
    defaults = {
        "model": f"HP LaserJet {random_lower_string()[:4]}",
        "serial_number": f"SN-{random_lower_string()[:10]}",
        "manufacturer": "HP",
        "customer_id": customer_id,
    }
    defaults.update(overrides)
    return equipment_repo.create_equipment(
        session=db, equipment_in=EquipmentCreate(**defaults)
    )
