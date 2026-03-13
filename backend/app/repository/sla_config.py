from sqlmodel import Session, select

from app.domain.sla_config import SLAConfigCreate
from app.models.sla_config import SLAConfig


def get_sla_config_by_segment(*, session: Session, segment: str) -> SLAConfig | None:
    return session.exec(
        select(SLAConfig).where(SLAConfig.segment == segment)
    ).first()


def get_all_sla_configs(*, session: Session) -> list[SLAConfig]:
    return list(session.exec(select(SLAConfig)).all())


def upsert_sla_config(*, session: Session, config_in: SLAConfigCreate) -> SLAConfig:
    existing = get_sla_config_by_segment(session=session, segment=config_in.segment)
    if existing:
        existing.sqlmodel_update(config_in.model_dump(exclude={"segment"}))
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    db_config = SLAConfig.model_validate(config_in)
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config
