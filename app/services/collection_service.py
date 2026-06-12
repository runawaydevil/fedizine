import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.registry import get_connector
from app.editorial.dedup import item_exists
from app.editorial.normalizer import normalize_raw_item
from app.editorial.scorer import apply_scoring
from app.models.item import Item
from app.models.job import Job
from app.models.source import Source


def _persist_item(db: Session, editorial, source: Source) -> bool:
    if item_exists(db, source.user_id, editorial.external_id):
        return False

    item = Item(
        user_id=source.user_id,
        source_id=source.id,
        external_id=editorial.external_id,
        platform=editorial.platform,
        content_type=editorial.content_type,
        title=editorial.title,
        content=editorial.content,
        summary=editorial.summary,
        canonical_url=editorial.canonical_url,
        author_name=editorial.author_name,
        author_handle=editorial.author_handle,
        published_at=editorial.published_at,
        media=[m.model_dump() for m in editorial.media],
        tags=editorial.tags,
        metrics=editorial.metrics,
        raw_data=editorial.raw_data,
        status=editorial.status,
        visibility=editorial.visibility,
    )
    apply_scoring(item, source)
    db.add(item)
    return True


async def _fetch_source_async(source: Source) -> list[dict]:
    connector = get_connector(source.platform)
    return await connector.fetch(source)


def collect_source(db: Session, source: Source) -> int:
    job = Job(
        user_id=source.user_id,
        job_type="collect",
        status="running",
        payload={"source_id": str(source.id)},
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()

    count = 0
    try:
        raw_items = asyncio.run(_fetch_source_async(source))
        for raw in raw_items:
            editorial = normalize_raw_item(
                raw, source.user_id, source.id, source.platform
            )
            if _persist_item(db, editorial, source):
                count += 1

        source.last_checked_at = datetime.now(timezone.utc)
        job.status = "completed"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise

    return count


def collect_source_by_id(db: Session, source_id: uuid.UUID) -> int:
    source = db.get(Source, source_id)
    if not source or not source.enabled:
        return 0
    return collect_source(db, source)


def collect_all_sources(db: Session, user_id: uuid.UUID) -> int:
    sources = db.scalars(
        select(Source).where(Source.user_id == user_id, Source.enabled.is_(True))
    ).all()
    total = 0
    for source in sources:
        total += collect_source(db, source)
    return total
