import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models.user import User
from app.domain.service_request import (
    ServiceRequestCreate,
    ServiceRequestPublic,
    ServiceRequestsPublic,
    ServiceRequestStatusUpdate,
    ServiceRequestUpdate,
)
from app.repository import customer as customer_repo
from app.repository import service_request as sr_repo

router = APIRouter(prefix="/service-requests", tags=["service-requests"])


@router.get("/", response_model=ServiceRequestsPublic)
def read_service_requests(
    session: SessionDep,
    _: User = Depends(require_permission("service_request", "view")),
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    priority: str | None = None,
    customer_id: uuid.UUID | None = None,
    assigned_engineer_id: uuid.UUID | None = None,
):
    items = sr_repo.get_service_requests(
        session=session,
        skip=skip,
        limit=limit,
        status=status,
        priority=priority,
        customer_id=customer_id,
        assigned_engineer_id=assigned_engineer_id,
    )
    count = sr_repo.get_service_requests_count(
        session=session,
        status=status,
        priority=priority,
        customer_id=customer_id,
        assigned_engineer_id=assigned_engineer_id,
    )
    return ServiceRequestsPublic(
        data=[ServiceRequestPublic.model_validate(r) for r in items],
        count=count,
    )


@router.post("/", response_model=ServiceRequestPublic)
def create_service_request(
    session: SessionDep,
    request_in: ServiceRequestCreate,
    current_user: CurrentUser,
    _: User = Depends(require_permission("service_request", "create")),
):
    customer = customer_repo.get_customer_by_id(
        session=session, customer_id=request_in.customer_id
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    sr = sr_repo.create_service_request(
        session=session,
        request_in=request_in,
        created_by=current_user.id,
    )
    return ServiceRequestPublic.model_validate(sr)


@router.get("/{request_id}", response_model=ServiceRequestPublic)
def read_service_request(
    request_id: uuid.UUID,
    session: SessionDep,
    _: User = Depends(require_permission("service_request", "view")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")
    return ServiceRequestPublic.model_validate(sr)


@router.patch("/{request_id}", response_model=ServiceRequestPublic)
def update_service_request(
    request_id: uuid.UUID,
    session: SessionDep,
    request_in: ServiceRequestUpdate,
    _: User = Depends(require_permission("service_request", "edit")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")
    sr = sr_repo.update_service_request(
        session=session, db_request=sr, request_in=request_in
    )
    return ServiceRequestPublic.model_validate(sr)


@router.post("/{request_id}/status", response_model=ServiceRequestPublic)
def update_service_request_status(
    request_id: uuid.UUID,
    session: SessionDep,
    status_update: ServiceRequestStatusUpdate,
    _: User = Depends(require_permission("service_request", "edit")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")
    try:
        sr = sr_repo.transition_status(
            session=session,
            db_request=sr,
            new_status=status_update.status,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ServiceRequestPublic.model_validate(sr)


@router.post("/{request_id}/assign", response_model=ServiceRequestPublic)
def assign_engineer(
    request_id: uuid.UUID,
    session: SessionDep,
    engineer_id: uuid.UUID,
    _: User = Depends(require_permission("service_request", "edit")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")

    from app.repository import user as user_repo

    engineer = user_repo.get_user_by_id(session=session, user_id=engineer_id)
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer not found")

    sr = sr_repo.update_service_request(
        session=session,
        db_request=sr,
        request_in=ServiceRequestUpdate(
            assigned_engineer_id=engineer_id, status="assigned"
        ),
    )
    return ServiceRequestPublic.model_validate(sr)
