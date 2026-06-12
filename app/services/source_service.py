import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source
from app.schemas.source import SourceCreate, SourceUpdate
from app.utils.url_validator import URLValidationError, validate_external_url


def list_sources(db: Session, user_id: uuid.UUID) -> list[Source]:
    return list(
        db.scalars(
            select(Source).where(Source.user_id == user_id).order_by(Source.name)
        ).all()
    )


def get_source(db: Session, user_id: uuid.UUID, source_id: uuid.UUID) -> Source | None:
    return db.scalar(
        select(Source).where(Source.id == source_id, Source.user_id == user_id)
    )


def create_source(db: Session, user_id: uuid.UUID, data: SourceCreate) -> Source:
    try:
        validate_external_url(data.url)
    except URLValidationError as exc:
        raise ValueError(str(exc)) from exc

    source = Source(
        user_id=user_id,
        name=data.name,
        platform=data.platform,
        source_type=data.source_type,
        url=data.url,
        handle=data.handle,
        config=data.config,
        enabled=data.enabled,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def update_source(
    db: Session, user_id: uuid.UUID, source_id: uuid.UUID, data: SourceUpdate
) -> Source | None:
    source = get_source(db, user_id, source_id)
    if not source:
        return None

    updates = data.model_dump(exclude_unset=True)
    if "url" in updates:
        validate_external_url(updates["url"])

    for key, value in updates.items():
        setattr(source, key, value)

    db.commit()
    db.refresh(source)
    return source


def delete_source(db: Session, user_id: uuid.UUID, source_id: uuid.UUID) -> bool:
    source = get_source(db, user_id, source_id)
    if not source:
        return False
    db.delete(source)
    db.commit()
    return True
