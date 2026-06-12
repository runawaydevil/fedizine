from pathlib import Path

from fastapi.templating import Jinja2Templates

from app.core.config import get_settings
from app.editorial.copy import MONTH_NAMES

settings = get_settings()
templates = Jinja2Templates(directory=str(settings.templates_dir))


def _month_name(period: str) -> str:
    try:
        return MONTH_NAMES[int(period.split("-")[1])]
    except (ValueError, KeyError, IndexError):
        return period


templates.env.filters["month_name"] = _month_name


def ensure_template_dirs() -> None:
    for sub in ("public", "admin", "print", "feeds", "partials"):
        (settings.templates_dir / sub).mkdir(parents=True, exist_ok=True)
