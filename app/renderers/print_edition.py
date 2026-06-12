from weasyprint import HTML

from app.core.config import get_settings
from app.models.edition import Edition
from app.renderers.common import group_edition_by_section, make_jinja_env

settings = get_settings()

_env = make_jinja_env(autoescape=["html", "xml"])


def render_pdf(edition: Edition) -> bytes:
    template = _env.get_template("print/zine_a5.html")
    html_content = template.render(
        edition=edition,
        sections=group_edition_by_section(edition),
        app_name=settings.app_name,
        public_url=settings.app_public_url,
    )
    css_path = settings.static_dir / "css" / "print-a5.css"
    stylesheets = [str(css_path)] if css_path.exists() else []
    return HTML(string=html_content, base_url=str(settings.templates_dir)).write_pdf(
        stylesheets=stylesheets
    )
