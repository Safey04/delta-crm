import uuid

from sqlmodel import Session, func, select

from app.domain.service_visit import ServiceVisitCreate, ServiceVisitUpdate
from app.models.service_visit import ServiceVisit


def create_service_visit(
    *, session: Session, visit_in: ServiceVisitCreate, engineer_id: uuid.UUID
) -> ServiceVisit:
    db_visit = ServiceVisit.model_validate(
        visit_in, update={"engineer_id": engineer_id}
    )
    session.add(db_visit)
    session.commit()
    session.refresh(db_visit)
    return db_visit


def get_service_visit_by_id(
    *, session: Session, visit_id: uuid.UUID
) -> ServiceVisit | None:
    return session.get(ServiceVisit, visit_id)


def get_visits_by_service_request(
    *, session: Session, service_request_id: uuid.UUID
) -> list[ServiceVisit]:
    return list(
        session.exec(
            select(ServiceVisit)
            .where(ServiceVisit.service_request_id == service_request_id)
            .order_by(ServiceVisit.visit_date.desc())  # type: ignore[union-attr]
        ).all()
    )


def get_visits_count_by_service_request(
    *, session: Session, service_request_id: uuid.UUID
) -> int:
    return session.exec(
        select(func.count())
        .select_from(ServiceVisit)
        .where(ServiceVisit.service_request_id == service_request_id)
    ).one()


def update_service_visit(
    *, session: Session, db_visit: ServiceVisit, visit_in: ServiceVisitUpdate
) -> ServiceVisit:
    visit_data = visit_in.model_dump(exclude_unset=True)
    db_visit.sqlmodel_update(visit_data)
    session.add(db_visit)
    session.commit()
    session.refresh(db_visit)
    return db_visit
