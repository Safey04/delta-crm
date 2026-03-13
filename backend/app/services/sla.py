from datetime import timedelta

from sqlmodel import Session

from app.domain.utils import get_datetime_utc
from app.models.service_request import ServiceRequest
from app.repository import sla_config as sla_repo

# Default SLA hours if no config found
DEFAULT_SLA = {
    "enterprise": {"response": 2, "resolution": 24},
    "smb": {"response": 4, "resolution": 48},
    "walk_in": {"response": 8, "resolution": 72},
}


def apply_sla_deadlines(
    *, session: Session, service_request: ServiceRequest, customer_segment: str
) -> ServiceRequest:
    """Set SLA deadlines on a service request based on customer segment."""
    config = sla_repo.get_sla_config_by_segment(
        session=session, segment=customer_segment
    )

    if config:
        response_hours = config.response_hours
        resolution_hours = config.resolution_hours
    else:
        defaults = DEFAULT_SLA.get(customer_segment, DEFAULT_SLA["walk_in"])
        response_hours = defaults["response"]
        resolution_hours = defaults["resolution"]

    now = get_datetime_utc()
    service_request.sla_response_due = now + timedelta(hours=response_hours)
    service_request.sla_resolution_due = now + timedelta(hours=resolution_hours)

    session.add(service_request)
    session.commit()
    session.refresh(service_request)
    return service_request
