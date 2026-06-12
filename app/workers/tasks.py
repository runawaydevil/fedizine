import uuid

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.user import User
from app.services.collection_service import collect_all_sources, collect_source_by_id
from app.services.edition_service import (
    build_edition,
    get_edition_with_items,
    get_or_create_edition,
)
from app.services.publish_service import build_pdf, publish_edition
from app.services.scoring_service import score_user_items
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.collect_source")
def collect_source(source_id: str) -> int:
    with SessionLocal() as db:
        return collect_source_by_id(db, uuid.UUID(source_id))


@celery_app.task(name="app.workers.tasks.collect_all_users")
def collect_all_users() -> int:
    total = 0
    with SessionLocal() as db:
        users = db.scalars(select(User).where(User.is_active.is_(True))).all()
        for user in users:
            total += collect_all_sources(db, user.id)
    return total


@celery_app.task(name="app.workers.tasks.score_items")
def score_items(user_id: str, month: str | None = None) -> int:
    with SessionLocal() as db:
        return score_user_items(db, uuid.UUID(user_id), month)


@celery_app.task(name="app.workers.tasks.build_edition_task")
def build_edition_task(user_id: str, month: str) -> int:
    with SessionLocal() as db:
        edition = get_or_create_edition(db, uuid.UUID(user_id), month)
        return build_edition(db, edition)


@celery_app.task(name="app.workers.tasks.build_pdf_task")
def build_pdf_task(edition_id: str) -> str:
    with SessionLocal() as db:
        edition = get_edition_with_items(db, uuid.UUID(edition_id))
        if not edition:
            return ""
        return build_pdf(db, edition)


@celery_app.task(name="app.workers.tasks.publish_edition_task")
def publish_edition_task(edition_id: str) -> dict:
    with SessionLocal() as db:
        edition = get_edition_with_items(db, uuid.UUID(edition_id))
        if not edition:
            return {}
        return publish_edition(db, edition)
