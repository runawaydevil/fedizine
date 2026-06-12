from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.edition import Edition
from app.models.zine import Zine
from app.renderers.feed_rss import render_feed
from app.renderers.print_edition import render_pdf
from app.renderers.web_edition import render_edition_html, render_home, write_public_file

settings = get_settings()


def build_pdf(db: Session, edition: Edition) -> str:
    pdf_bytes = render_pdf(edition)
    public_dir = Path(settings.public_path) / edition.period_year_month
    public_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = public_dir / "zine.pdf"
    pdf_path.write_bytes(pdf_bytes)

    zine = edition.zine
    if not zine:
        zine = Zine(user_id=edition.user_id, edition_id=edition.id)
        db.add(zine)
        edition.zine = zine

    zine.pdf_path = str(pdf_path)
    zine.generated_at = datetime.now(timezone.utc)
    db.commit()
    return str(pdf_path)


def publish_edition(db: Session, edition: Edition) -> dict:
    html = render_edition_html(edition)
    period = edition.period_year_month
    write_public_file(period, "index.html", html)

    pdf_path = build_pdf(db, edition)

    feed_xml = render_feed([edition])
    write_public_file("", "feed.xml", feed_xml)

    home_html = render_home(db, edition.user_id)
    write_public_file("", "index.html", home_html)

    edition.status = "published"
    edition.visibility = "public"
    edition.published_at = datetime.now(timezone.utc)

    zine = edition.zine
    if zine:
        zine.web_path = f"/{period}/"
        zine.published_at = edition.published_at

    db.commit()

    base = settings.app_public_url.rstrip("/")
    return {
        "web_url": f"{base}/{period}/",
        "pdf_url": f"{base}/{period}/zine.pdf",
        "pdf_path": pdf_path,
    }
