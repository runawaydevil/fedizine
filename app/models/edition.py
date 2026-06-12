import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Edition(Base):
    __tablename__ = "editions"
    __table_args__ = (
        UniqueConstraint("user_id", "period_year_month", name="uq_editions_user_period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    editorial_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    period_year_month: Mapped[str] = mapped_column(String(7), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    visibility: Mapped[str] = mapped_column(String(32), default="private")
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sections_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("User", back_populates="editions")
    edition_items = relationship(
        "EditionItem", back_populates="edition", cascade="all, delete-orphan"
    )
    zine = relationship("Zine", back_populates="edition", uselist=False)


class EditionItem(Base):
    __tablename__ = "edition_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    edition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("editions.id"), nullable=False, index=True
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id"), nullable=False, index=True
    )
    section: Mapped[str] = mapped_column(String(64), default="Fragments")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    override_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    override_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    edition = relationship("Edition", back_populates="edition_items")
    item = relationship("Item", back_populates="edition_links")
