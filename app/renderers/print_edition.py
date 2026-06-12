from weasyprint import HTML

from app.core.config import get_settings
from app.editorial.copy import month_label
from app.models.edition import Edition
from app.renderers.common import (
    attach_issue_filters,
    attach_month_filter,
    edition_stats,
    editorial_note,
    issue_toc_entries,
    make_jinja_env,
    public_issue_sections,
)
from app.renderers.web_edition import site_host_from_url

settings = get_settings()

_env = make_jinja_env(autoescape=["html", "xml"])
attach_month_filter(_env)
attach_issue_filters(_env)


def render_pdf(edition: Edition) -> bytes:
    template = _env.get_template("print/zine_a5.html")
    month = month_label(edition.period_year_month)
    sections = public_issue_sections(edition)
    fragment_count, source_count = edition_stats(edition)
    html_content = template.render(
        edition=edition,
        sections=sections,
        toc_entries=issue_toc_entries(sections),
        editorial_note=editorial_note(edition, month),
        fragment_count=fragment_count,
        source_count=source_count,
        app_name=settings.app_name,
        public_url=settings.app_public_url,
        site_host=site_host_from_url(settings.app_public_url),
        month_label=month,
    )
    css_path = settings.static_dir / "css" / "print-a5.css"
    stylesheets = [str(css_path)] if css_path.exists() else []
    return HTML(string=html_content, base_url=str(settings.templates_dir)).write_pdf(
        stylesheets=stylesheets
    )
