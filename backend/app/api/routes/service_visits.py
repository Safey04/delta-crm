import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, require_permission
from app.domain.service_visit import (
    ServiceVisitCreate,
    ServiceVisitPublic,
    ServiceVisitsPublic,
    ServiceVisitUpdate,
)
from app.repository import service_request as sr_repo
from app.repository import service_visit as visit_repo

router = APIRouter(
    prefix="/service-requests/{request_id}/visits",
    tags=["service-visits"],
)


@router.get("/", response_model=ServiceVisitsPublic)
def read_visits(
    request_id: uuid.UUID,
    session: SessionDep,
    _: CurrentUser = Depends(require_permission("service_request", "view")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")
    visits = visit_repo.get_visits_by_service_request(
        session=session,
        service_request_id=request_id,
    )
    count = visit_repo.get_visits_count_by_service_request(
        session=session,
        service_request_id=request_id,
    )
    return ServiceVisitsPublic(
        data=[ServiceVisitPublic.model_validate(v) for v in visits],
        count=count,
    )


@router.post("/", response_model=ServiceVisitPublic)
def create_visit(
    request_id: uuid.UUID,
    session: SessionDep,
    visit_in: ServiceVisitCreate,
    current_user: CurrentUser,
    _: CurrentUser = Depends(require_permission("service_request", "edit")),
):
    sr = sr_repo.get_service_request_by_id(session=session, request_id=request_id)
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")
    if visit_in.service_request_id != request_id:
        raise HTTPException(status_code=400, detail="Service request ID mismatch")

    visit = visit_repo.create_service_visit(
        session=session,
        visit_in=visit_in,
        engineer_id=current_user.id,
    )
    return ServiceVisitPublic.model_validate(visit)


@router.patch("/{visit_id}", response_model=ServiceVisitPublic)
def update_visit(
    request_id: uuid.UUID,
    visit_id: uuid.UUID,
    session: SessionDep,
    visit_in: ServiceVisitUpdate,
    _: CurrentUser = Depends(require_permission("service_request", "edit")),
):
    visit = visit_repo.get_service_visit_by_id(session=session, visit_id=visit_id)
    if not visit or visit.service_request_id != request_id:
        raise HTTPException(status_code=404, detail="Service visit not found")
    visit = visit_repo.update_service_visit(
        session=session,
        db_visit=visit,
        visit_in=visit_in,
    )
    return ServiceVisitPublic.model_validate(visit)
