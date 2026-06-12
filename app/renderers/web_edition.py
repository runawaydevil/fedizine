from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.editorial.copy import month_label
from app.models.edition import Edition
from app.models.source import Source
from app.models.user import User
from app.renderers.common import attach_month_filter, group_edition_by_section, make_jinja_env
from app.services.edition_service import list_published_editions

settings = get_settings()

_env = make_jinja_env(autoescape=["html", "xml"])
attach_month_filter(_env)


def site_host_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc or url.replace("https://", "").replace("http://", "").rstrip("/")


def _month_label(period: str) -> str:
    return month_label(period)


def _editions_by_year(editions: list[Edition]) -> dict[str, list[Edition]]:
    grouped: dict[str, list[Edition]] = {}
    for ed in editions:
        year = ed.period_year_month.split("-")[0]
        grouped.setdefault(year, []).append(ed)
    return grouped


def _pdf_ready(edition: Edition | None) -> bool:
    if not edition:
        return False
    if edition.zine and edition.zine.pdf_path:
        return Path(edition.zine.pdf_path).exists()
    fallback = Path(settings.public_path) / edition.period_year_month / "zine.pdf"
    return fallback.exists()


def build_home_context(db: Session, user_id) -> dict:
    user = db.get(User, user_id) if user_id else None
    editions = list_published_editions(db, user_id) if user_id else []
    latest = None
    fragment_count = 0
    source_count = 0

    if editions:
        latest = db.scalar(
            select(Edition)
            .options(
                joinedload(Edition.edition_items),
                joinedload(Edition.zine),
            )
            .where(Edition.id == editions[0].id)
        )
        if latest:
            fragment_count = len(latest.edition_items)
            source_count = db.scalar(
                select(func.count())
                .select_from(Source)
                .where(Source.user_id == user_id, Source.enabled.is_(True))
            ) or 0

    return {
        "user": user,
        "editions": editions,
        "latest": latest,
        "fragment_count": fragment_count,
        "source_count": source_count,
        "pdf_ready": _pdf_ready(latest),
        "month_label": _month_label(latest.period_year_month) if latest else None,
        "editions_by_year": _editions_by_year(editions),
        "app_name": settings.app_name,
        "public_url": settings.app_public_url,
        "site_host": site_host_from_url(settings.app_public_url),
    }


def render_edition_html(edition: Edition) -> str:
    template = _env.get_template("public/edition.html")
    return template.render(
        edition=edition,
        sections=group_edition_by_section(edition),
        app_name=settings.app_name,
        public_url=settings.app_public_url,
        site_host=site_host_from_url(settings.app_public_url),
        month_label=_month_label(edition.period_year_month),
        pdf_ready=_pdf_ready(edition),
    )


def render_home(db: Session, user_id) -> str:
    template = _env.get_template("public/home.html")
    return template.render(**build_home_context(db, user_id))


def render_archive(db: Session, user_id) -> str:
    editions = list_published_editions(db, user_id)
    template = _env.get_template("public/archive.html")
    return template.render(
        editions=editions,
        editions_by_year=_editions_by_year(editions),
        app_name=settings.app_name,
        public_url=settings.app_public_url,
        site_host=site_host_from_url(settings.app_public_url),
    )


def render_colophon() -> str:
    template = _env.get_template("public/colophon.html")
    return template.render(
        app_name=settings.app_name,
        public_url=settings.app_public_url,
        site_host=site_host_from_url(settings.app_public_url),
    )


def render_slash_page(
    slug: str,
    title: str,
    lede: str,
    page_body: list[str] | None = None,
) -> str:
    template = _env.get_template("public/slash.html")
    return template.render(
        slug=slug,
        page_title=title,
        page_lede=lede,
        page_body=page_body or [],
        app_name=settings.app_name,
        public_url=settings.app_public_url,
        site_host=site_host_from_url(settings.app_public_url),
    )


def write_public_file(period: str, filename: str, content: str) -> Path:
    base = Path(settings.public_path)
    if period:
        target_dir = base / period
    else:
        target_dir = base
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / filename
    path.write_text(content, encoding="utf-8")
    return path
