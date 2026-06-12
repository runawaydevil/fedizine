from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EditionCreate(BaseModel):
    period_year_month: str
    title: str | None = None
    editorial_text: str | None = None


class EditionItemAdd(BaseModel):
    item_id: UUID
    section: str = "Fragments"
    sort_order: int = 0
    is_featured: bool = False


class EditionRead(BaseModel):
    id: UUID
    slug: str
    title: str
    period_year_month: str
    status: str
    visibility: str
    published_at: datetime | None

    model_config = {"from_attributes": True}
