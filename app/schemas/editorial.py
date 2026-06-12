from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MediaRef(BaseModel):
    type: str = "image"
    url: str
    alt: str | None = None
    local_path: str | None = None


class EditorialItemSchema(BaseModel):
    external_id: str
    user_id: UUID
    source_id: UUID
    network: str = "fediverse"
    platform: str
    content_type: str = "status"
    title: str | None = None
    content: str = ""
    summary: str | None = None
    canonical_url: str | None = None
    author_name: str | None = None
    author_handle: str | None = None
    published_at: datetime | None = None
    media: list[MediaRef] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)
    score: int = 0
    status: str = "candidate"
    visibility: str = "public"
    suggested_section: str | None = None
    raw_data: dict = Field(default_factory=dict)
