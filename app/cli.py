import uuid
from datetime import datetime, timezone

import typer
from slugify import slugify
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.services.collection_service import collect_all_sources, collect_source_by_id
from app.services.edition_service import (
    build_edition,
    get_edition_with_items,
    get_or_create_edition,
)
from app.services.publish_service import build_pdf, publish_edition
from app.services.scoring_service import score_user_items

app = typer.Typer(help="Fedizine — editorial tools")
settings = get_settings()


def _get_user(db, slug: str | None = None) -> User:
    target_slug = slug or settings.default_user_slug
    user = db.scalar(select(User).where(User.slug == target_slug))
    if not user:
        raise typer.Exit(f"User '{target_slug}' not found. Run create-user first.")
    return user


@app.command("create-user")
def create_user(
    email: str = typer.Option(None, help="Editor email"),
    name: str = typer.Option(None, help="Display name"),
    slug: str = typer.Option(None, help="Public slug"),
    password: str = typer.Option(..., prompt=True, hide_input=True),
):
    """Create the initial editorial user."""
    email = email or settings.default_user_email
    name = name or settings.default_user_name
    slug = slug or settings.default_user_slug

    with SessionLocal() as db:
        existing = db.scalar(select(User).where((User.email == email) | (User.slug == slug)))
        if existing:
            typer.echo(f"User already exists: {existing.email} ({existing.slug})")
            raise typer.Exit(1)

        user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=name,
            slug=slug,
            timezone=settings.default_timezone,
            locale=settings.default_locale,
        )
        db.add(user)
        db.commit()
        typer.echo(f"User created: {user.display_name} <{user.email}> [{user.slug}]")


@app.command("collect")
def collect(
    user: str = typer.Option(None, "--user", help="User slug"),
    source_id: str = typer.Option(None, "--source", help="Source UUID"),
):
    """Collect fragments from Fediverse sources."""
    with SessionLocal() as db:
        editor = _get_user(db, user)
        if source_id:
            count = collect_source_by_id(db, uuid.UUID(source_id))
            typer.echo(f"Collected {count} fragments from source.")
        else:
            count = collect_all_sources(db, editor.id)
            typer.echo(f"Collected {count} fragments total.")


@app.command("score")
def score(
    user: str = typer.Option(None, "--user", help="User slug"),
    month: str = typer.Option(None, "--month", help="Period YYYY-MM"),
):
    """Score fragments for editorial selection."""
    with SessionLocal() as db:
        editor = _get_user(db, user)
        count = score_user_items(db, editor.id, month)
        typer.echo(f"Scored {count} fragments.")


@app.command("build-edition")
def build_edition_cmd(
    user: str = typer.Option(None, "--user"),
    month: str = typer.Option(..., "--month"),
):
    """Build issue draft from selected fragments."""
    with SessionLocal() as db:
        editor = _get_user(db, user)
        edition = get_or_create_edition(db, editor.id, month)
        added = build_edition(db, edition)
        typer.echo(f"Issue {edition.period_year_month}: {added} items assembled.")


@app.command("build-pdf")
def build_pdf_cmd(
    user: str = typer.Option(None, "--user"),
    month: str = typer.Option(..., "--month"),
):
    """Generate issue PDF."""
    with SessionLocal() as db:
        editor = _get_user(db, user)
        edition = get_or_create_edition(db, editor.id, month)
        edition = get_edition_with_items(db, edition.id)
        path = build_pdf(db, edition)
        typer.echo(f"PDF generated: {path}")


@app.command("publish")
def publish_cmd(
    user: str = typer.Option(None, "--user"),
    month: str = typer.Option(..., "--month"),
):
    """Publish issue (web + PDF)."""
    with SessionLocal() as db:
        editor = _get_user(db, user)
        edition = get_or_create_edition(db, editor.id, month)
        edition = get_edition_with_items(db, edition.id)
        result = publish_edition(db, edition)
        typer.echo(f"Issue published: {result['web_url']}")


if __name__ == "__main__":
    app()
