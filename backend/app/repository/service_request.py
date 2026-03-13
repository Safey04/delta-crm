import uuid

from sqlmodel import Session, func, select

from app.domain.service_request import ServiceRequestCreate, ServiceRequestUpdate
from app.domain.utils import get_datetime_utc
from app.models.service_request import ServiceRequest

# Valid status transitions
VALID_TRANSITIONS: dict[str, list[str]] = {
    "new": ["quoted", "assigned", "closed"],
    "quoted": ["approved", "closed"],
    "approved": ["assigned", "closed"],
    "assigned": ["in_progress", "closed"],
    "in_progress": ["completed", "assigned"],  # can reassign
    "completed": ["invoiced", "closed"],
    "invoiced": ["closed"],
    "closed": [],  # terminal state
}


def create_service_request(
    *, session: Session, request_in: ServiceRequestCreate, created_by: uuid.UUID
) -> ServiceRequest:
    db_request = ServiceRequest.model_validate(
        request_in, update={"created_by": created_by}
    )
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request


def get_service_request_by_id(
    *, session: Session, request_id: uuid.UUID
) -> ServiceRequest | None:
    return session.get(ServiceRequest, request_id)


def get_service_requests(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    priority: str | None = None,
    customer_id: uuid.UUID | None = None,
    assigned_engineer_id: uuid.UUID | None = None,
) -> list[ServiceRequest]:
    query = select(ServiceRequest)
    if status:
        query = query.where(ServiceRequest.status == status)
    if priority:
        query = query.where(ServiceRequest.priority == priority)
    if customer_id:
        query = query.where(ServiceRequest.customer_id == customer_id)
    if assigned_engineer_id:
        query = query.where(ServiceRequest.assigned_engineer_id == assigned_engineer_id)
    return list(
        session.exec(
            query.order_by(ServiceRequest.created_at.desc())  # type: ignore[union-attr]
            .offset(skip)
            .limit(limit)
        ).all()
    )


def get_service_requests_count(
    *,
    session: Session,
    status: str | None = None,
    priority: str | None = None,
    customer_id: uuid.UUID | None = None,
    assigned_engineer_id: uuid.UUID | None = None,
) -> int:
    query = select(func.count()).select_from(ServiceRequest)
    if status:
        query = query.where(ServiceRequest.status == status)
    if priority:
        query = query.where(ServiceRequest.priority == priority)
    if customer_id:
        query = query.where(ServiceRequest.customer_id == customer_id)
    if assigned_engineer_id:
        query = query.where(ServiceRequest.assigned_engineer_id == assigned_engineer_id)
    return session.exec(query).one()


def update_service_request(
    *,
    session: Session,
    db_request: ServiceRequest,
    request_in: ServiceRequestUpdate,
) -> ServiceRequest:
    request_data = request_in.model_dump(exclude_unset=True)
    db_request.sqlmodel_update(request_data)
    db_request.updated_at = get_datetime_utc()
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request


def transition_status(
    *, session: Session, db_request: ServiceRequest, new_status: str
) -> ServiceRequest:
    """Validate and apply a status transition."""
    allowed = VALID_TRANSITIONS.get(db_request.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from '{db_request.status}' to '{new_status}'. "
            f"Allowed: {allowed}"
        )
    db_request.status = new_status
    db_request.updated_at = get_datetime_utc()
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request
