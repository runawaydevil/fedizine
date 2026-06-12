from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.item import Item


def item_exists(db: Session, user_id, external_id: str) -> bool:
    existing = db.scalar(
        select(Item.id).where(
            Item.user_id == user_id,
            Item.external_id == external_id,
        )
    )
    return existing is not None
