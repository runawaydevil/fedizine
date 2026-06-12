from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import get_settings
from app.editorial.copy import MONTH_NAMES
from app.models.edition import Edition

settings = get_settings()


def make_jinja_env(*, autoescape: list[str]) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(settings.templates_dir)),
        autoescape=select_autoescape(autoescape),
    )


def attach_month_filter(env: Environment) -> None:
    env.filters["month_name"] = lambda period: (
        MONTH_NAMES.get(int(period.split("-")[1]), period)
        if "-" in period
        else period
    )


def group_edition_by_section(edition: Edition) -> dict[str, list]:
    sections: dict[str, list] = {}
    for ei in sorted(edition.edition_items, key=lambda x: (x.section, x.sort_order)):
        sections.setdefault(ei.section, []).append(ei)
    return sections
