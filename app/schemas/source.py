from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class SourceCreate(BaseModel):
    name: str
    platform: str
    source_type: str = "feed"
    url: str
    handle: str | None = None
    config: dict = Field(default_factory=dict)
    enabled: bool = True


class SourceUpdate(BaseModel):
    name: str | None = None
    platform: str | None = None
    source_type: str | None = None
    url: str | None = None
    handle: str | None = None
    config: dict | None = None
    enabled: bool | None = None


class SourceRead(BaseModel):
    id: UUID
    name: str
    platform: str
    source_type: str
    url: str
    handle: str | None
    enabled: bool

    model_config = {"from_attributes": True}
