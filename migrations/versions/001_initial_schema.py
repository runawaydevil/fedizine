"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("locale", sa.String(16), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("handle", sa.String(255), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sources_user_id", "sources", ["user_id"])
    op.create_table(
        "items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(512), nullable=False),
        sa.Column("platform", sa.String(64), nullable=False),
        sa.Column("content_type", sa.String(64), nullable=True),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.String(2048), nullable=True),
        sa.Column("author_name", sa.String(255), nullable=True),
        sa.Column("author_handle", sa.String(255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("media", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=True),
        sa.Column("visibility", sa.String(32), nullable=True),
        sa.Column("suggested_section", sa.String(64), nullable=True),
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "external_id", name="uq_items_user_external"),
    )
    op.create_index("ix_items_user_id", "items", ["user_id"])
    op.create_index("ix_items_source_id", "items", ["source_id"])
    op.create_index("ix_items_status", "items", ["status"])
    op.create_table(
        "editions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(128), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("editorial_text", sa.Text(), nullable=True),
        sa.Column("period_year_month", sa.String(7), nullable=False),
        sa.Column("status", sa.String(32), nullable=True),
        sa.Column("visibility", sa.String(32), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sections_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "period_year_month", name="uq_editions_user_period"),
    )
    op.create_index("ix_editions_user_id", "editions", ["user_id"])
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])
    op.create_table(
        "edition_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("edition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("section", sa.String(64), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=True),
        sa.Column("override_title", sa.String(512), nullable=True),
        sa.Column("override_summary", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["edition_id"], ["editions.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_edition_items_edition_id", "edition_items", ["edition_id"])
    op.create_index("ix_edition_items_item_id", "edition_items", ["item_id"])
    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("media_type", sa.String(32), nullable=True),
        sa.Column("original_url", sa.String(2048), nullable=False),
        sa.Column("local_path", sa.String(1024), nullable=True),
        sa.Column("alt_text", sa.String(512), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_media_assets_user_id", "media_assets", ["user_id"])
    op.create_index("ix_media_assets_item_id", "media_assets", ["item_id"])
    op.create_table(
        "zines",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("edition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("web_path", sa.String(1024), nullable=True),
        sa.Column("pdf_path", sa.String(1024), nullable=True),
        sa.Column("json_path", sa.String(1024), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["edition_id"], ["editions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("edition_id"),
    )
    op.create_index("ix_zines_user_id", "zines", ["user_id"])


def downgrade() -> None:
    op.drop_table("zines")
    op.drop_table("media_assets")
    op.drop_table("edition_items")
    op.drop_table("jobs")
    op.drop_table("editions")
    op.drop_table("items")
    op.drop_table("sources")
    op.drop_table("users")
