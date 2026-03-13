import uuid

from sqlmodel import Session

from app.domain.service_request import ServiceRequestCreate
from app.models.service_request import ServiceRequest
from app.repository import service_request as sr_repo


def create_random_service_request(
    db: Session,
    customer_id: uuid.UUID,
    created_by: uuid.UUID,
    **overrides,
) -> ServiceRequest:
    defaults = {
        "description": "Printer not printing — paper jam indicator",
        "priority": "medium",
        "source": "phone",
        "customer_id": customer_id,
    }
    defaults.update(overrides)
    return sr_repo.create_service_request(
        session=db,
        request_in=ServiceRequestCreate(**defaults),
        created_by=created_by,
    )
