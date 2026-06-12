from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.models.item import Item
from app.models.source import Source


SECTION_MAP = {
    "image": "Photos",
    "album": "Photos",
    "book": "Readings",
    "review": "Readings",
    "video": "Videos",
    "event": "Agenda",
    "community_post": "Communities",
    "link": "Commented links",
    "article": "Fragments",
    "status": "Fragments",
    "note": "Fragments",
    "thread": "Fragments",
}


def score_item(item: Item, source: Source | None = None) -> tuple[int, str | None]:
    score = 0
    content = item.content or ""
    config = (source.config if source else {}) or {}

    if config.get("own_content") or item.author_handle == source.handle if source else False:
        score += 30

    if item.media:
        score += 20

    if item.content_type == "thread" or item.raw_data.get("in_reply_to"):
        score += 20

    if "http" in content and len(content) > 80:
        score += 15

    for m in item.media or []:
        if isinstance(m, dict) and m.get("alt"):
            score += 15
            break

    if item.tags:
        score += 10

    metrics = item.metrics or {}
    engagement = sum(metrics.get(k, 0) for k in ("replies", "boosts", "favorites"))
    score += min(engagement, 10)

    if item.published_at:
        age = datetime.now(timezone.utc) - item.published_at.replace(tzinfo=timezone.utc)
        if age < timedelta(days=7):
            score += 5

    if len(content) > 280:
        score += 10
    elif len(content) < 50:
        score -= 20

    if item.content_type in ("repost", "boost") and len(content) < 30:
        score -= 30

    section = SECTION_MAP.get(item.content_type, "Fragments")
    if item.content_type == "link" and len(content) < 40:
        section = "Commented links"

    return score, section


def apply_scoring(item: Item, source: Source | None = None) -> None:
    settings = get_settings()
    score, section = score_item(item, source)
    item.score = score
    item.suggested_section = section
    if score >= settings.editorial_score_threshold and item.status == "candidate":
        item.status = "selected"
