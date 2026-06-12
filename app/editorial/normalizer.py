import re
from datetime import datetime, timezone

import bleach
from bs4 import BeautifulSoup

from app.schemas.editorial import EditorialItemSchema, MediaRef


ALLOWED_TAGS = ["p", "br", "a", "em", "strong", "ul", "ol", "li", "blockquote"]
ALLOWED_ATTRS = {"a": ["href", "title"]}


def strip_html(html: str) -> str:
    if not html:
        return ""
    cleaned = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    soup = BeautifulSoup(cleaned, "html.parser")
    text = soup.get_text("\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_title(content: str, provided: str | None = None) -> str | None:
    if provided and provided.strip():
        return provided.strip()[:512]
    if not content:
        return None
    first_line = content.split("\n")[0].strip()
    if len(first_line) > 120:
        return first_line[:117] + "..."
    return first_line or None


def normalize_raw_item(
    raw: dict,
    user_id,
    source_id,
    platform: str,
) -> EditorialItemSchema:
    content_html = raw.get("content_html", "")
    content = strip_html(content_html) if content_html else raw.get("content", "")
    title = extract_title(content, raw.get("title"))

    media_list = []
    for m in raw.get("media", []):
        if isinstance(m, dict) and m.get("url"):
            media_list.append(
                MediaRef(
                    type=m.get("type", "image"),
                    url=m["url"],
                    alt=m.get("alt"),
                )
            )

    published = raw.get("published_at")
    if isinstance(published, str):
        published = datetime.fromisoformat(published.replace("Z", "+00:00"))

    return EditorialItemSchema(
        external_id=raw["external_id"],
        user_id=user_id,
        source_id=source_id,
        platform=platform,
        content_type=raw.get("content_type", "status"),
        title=title,
        content=content,
        summary=raw.get("summary"),
        canonical_url=raw.get("url"),
        author_name=raw.get("author_name"),
        author_handle=raw.get("author_handle"),
        published_at=published,
        media=media_list,
        tags=raw.get("tags", []),
        metrics=raw.get("metrics", {}),
        raw_data=raw.get("raw_data", raw),
        status="candidate",
    )
