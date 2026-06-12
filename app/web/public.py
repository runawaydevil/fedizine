from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import DbSession
from app.models.user import User
from app.renderers.feed_rss import render_feed
from app.renderers.web_edition import (
    build_home_context,
    render_archive,
    render_colophon,
    render_edition_html,
    render_slash_page,
    site_host_from_url,
)
from app.services.edition_service import get_published_edition, list_published_editions
from app.web.templates import templates

router = APIRouter(tags=["public"])
settings = get_settings()

SLASH_PAGES = {
    "about": (
        "About",
        "Who keeps this Fediverse webzine running.",
        [
            "Fedizine is a tiny monthly press that stitches together posts, photos, readings, and links from across the Fediverse.",
            "This page will grow into a proper introduction to the project, its editors, and why it exists.",
        ],
    ),
    "now": (
        "Now",
        "What is on the desk right now — current focus, readings, and projects.",
        [
            "A /now page is a small snapshot of attention: what matters this month, what is being read, and what is in progress.",
            "Check back as the editorial rhythm settles in.",
        ],
    ),
    "uses": (
        "Uses",
        "Tools, rituals, and small systems behind Fedizine.",
        [
            "This page will collect notes about the tools, rituals, and small systems behind Fedizine.",
            "Think feeds, print workflows, and the stack that turns fragments into issues.",
        ],
    ),
    "links": (
        "Links",
        "Neighbors, shortcuts, and corners of the personal web.",
        [
            "A curated list of friends, instances, and useful corners of the federated web.",
            "More links will land here as the press finds its orbit.",
        ],
    ),
}


def _default_user(db):
    return db.scalar(
        select(User).where(User.slug == settings.default_user_slug, User.is_active.is_(True))
    )


def _public_base_context():
    return {
        "app_name": settings.app_name,
        "public_url": settings.app_public_url,
        "site_host": site_host_from_url(settings.app_public_url),
    }


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: DbSession):
    user = _default_user(db)
    ctx = build_home_context(db, user.id if user else None)
    return templates.TemplateResponse(request, "public/home.html", ctx)


@router.get("/archive/", response_class=HTMLResponse)
def archive(request: Request, db: DbSession):
    user = _default_user(db)
    if not user:
        return HTMLResponse(render_archive(db, None))
    return HTMLResponse(render_archive(db, user.id))


@router.get("/colophon/", response_class=HTMLResponse)
def colophon(request: Request):
    return HTMLResponse(render_colophon())


@router.get("/feed.xml", response_class=HTMLResponse)
def feed_xml(db: DbSession):
    user = _default_user(db)
    editions = list_published_editions(db, user.id if user else None)
    return HTMLResponse(render_feed(editions), media_type="application/rss+xml")


@router.get("/about/", response_class=HTMLResponse)
def about_page():
    return HTMLResponse(render_slash_page("about", *SLASH_PAGES["about"]))


@router.get("/now/", response_class=HTMLResponse)
def now_page():
    return HTMLResponse(render_slash_page("now", *SLASH_PAGES["now"]))


@router.get("/uses/", response_class=HTMLResponse)
def uses_page():
    return HTMLResponse(render_slash_page("uses", *SLASH_PAGES["uses"]))


@router.get("/links/", response_class=HTMLResponse)
def links_page():
    return HTMLResponse(render_slash_page("links", *SLASH_PAGES["links"]))


@router.get("/{period}/", response_class=HTMLResponse)
def edition_page(request: Request, db: DbSession, period: str):
    if not _is_period(period):
        raise HTTPException(404)
    edition = get_published_edition(db, period)
    if not edition:
        raise HTTPException(404, "Edition not found.")
    return HTMLResponse(render_edition_html(edition))


@router.get("/{period}/zine.pdf")
def edition_pdf(period: str, db: DbSession):
    if not _is_period(period):
        raise HTTPException(404)
    edition = get_published_edition(db, period)
    if not edition or not edition.zine or not edition.zine.pdf_path:
        pdf_path = Path(settings.public_path) / period / "zine.pdf"
        if pdf_path.exists():
            return FileResponse(pdf_path, media_type="application/pdf", filename="zine.pdf")
        raise HTTPException(404, "PDF not found.")

    pdf_path = Path(edition.zine.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(404, "PDF not found.")
    return FileResponse(pdf_path, media_type="application/pdf", filename="zine.pdf")


def _is_period(value: str) -> bool:
    parts = value.split("-")
    if len(parts) != 2:
        return False
    try:
        year, month = int(parts[0]), int(parts[1])
        return 2000 <= year <= 2100 and 1 <= month <= 12
    except ValueError:
        return False
