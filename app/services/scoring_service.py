import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.editorial.scorer import apply_scoring
from app.models.item import Item
from app.models.source import Source


def score_user_items(
    db: Session, user_id: uuid.UUID, month: str | None = None
) -> int:
    query = (
        select(Item)
        .options(joinedload(Item.source))
        .where(Item.user_id == user_id, Item.status.in_(("candidate", "selected")))
    )

    if month:
        year, mon = map(int, month.split("-"))
        start = datetime(year, mon, 1)
        if mon == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, mon + 1, 1)
        query = query.where(
            Item.published_at >= start,
            Item.published_at < end,
        )

    items = db.scalars(query).all()
    for item in items:
        apply_scoring(item, item.source)

    db.commit()
    return len(items)
