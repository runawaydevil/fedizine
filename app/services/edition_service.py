import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.editorial.copy import (
    DEFAULT_SECTIONS,
    SECTION_FRAGMENTS,
    edition_title,
)
from app.models.edition import Edition, EditionItem
from app.models.item import Item


def get_or_create_edition(db: Session, user_id: uuid.UUID, period: str) -> Edition:
    edition = db.scalar(
        select(Edition).where(
            Edition.user_id == user_id,
            Edition.period_year_month == period,
        )
    )
    if edition:
        return edition

    title = edition_title(period)
    edition = Edition(
        user_id=user_id,
        slug=period,
        title=title,
        period_year_month=period,
        status="draft",
        visibility="private",
        sections_config={"sections": DEFAULT_SECTIONS},
    )
    db.add(edition)
    db.commit()
    db.refresh(edition)
    return edition


def build_edition(db: Session, edition: Edition) -> int:
    existing_item_ids = {
        ei.item_id
        for ei in db.scalars(
            select(EditionItem).where(EditionItem.edition_id == edition.id)
        ).all()
    }

    items = db.scalars(
        select(Item)
        .where(
            Item.user_id == edition.user_id,
            Item.status.in_(("selected", "featured")),
        )
        .order_by(Item.score.desc(), Item.published_at.desc())
    ).all()

    added = 0
    order = len(existing_item_ids)
    for item in items:
        if item.id in existing_item_ids:
            continue
        ei = EditionItem(
            edition_id=edition.id,
            item_id=item.id,
            section=item.suggested_section or SECTION_FRAGMENTS,
            sort_order=order,
            is_featured=item.status == "featured",
        )
        db.add(ei)
        order += 1
        added += 1

    edition.status = "ready"
    db.commit()
    return added


def get_edition_with_items(db: Session, edition_id: uuid.UUID) -> Edition | None:
    return db.scalar(
        select(Edition)
        .options(joinedload(Edition.edition_items).joinedload(EditionItem.item))
        .where(Edition.id == edition_id)
    )


def list_published_editions(db: Session, user_id: uuid.UUID | None = None) -> list[Edition]:
    query = select(Edition).where(Edition.status == "published")
    if user_id:
        query = query.where(Edition.user_id == user_id)
    return list(
        db.scalars(query.order_by(Edition.period_year_month.desc())).all()
    )


def get_published_edition(db: Session, period: str) -> Edition | None:
    return db.scalar(
        select(Edition)
        .options(
            joinedload(Edition.edition_items).joinedload(EditionItem.item),
            joinedload(Edition.zine),
        )
        .where(Edition.period_year_month == period, Edition.status == "published")
    )


def update_item_status(db: Session, user_id: uuid.UUID, item_id: uuid.UUID, status: str) -> Item | None:
    item = db.scalar(
        select(Item).where(Item.id == item_id, Item.user_id == user_id)
    )
    if not item:
        return None
    item.status = status
    db.commit()
    db.refresh(item)
    return item
