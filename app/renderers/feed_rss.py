from app.core.config import get_settings
from app.models.edition import Edition
from app.renderers.common import make_jinja_env
from app.renderers.web_edition import site_host_from_url

settings = get_settings()

_env = make_jinja_env(autoescape=["xml"])


def render_feed(editions: list[Edition]) -> str:
    template = _env.get_template("feeds/rss.xml")
    return template.render(
        editions=editions,
        app_name=settings.app_name,
        public_url=settings.app_public_url,
        site_host=site_host_from_url(settings.app_public_url),
    )
