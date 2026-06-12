from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import httpx

from app.connectors.base import Connector
from app.core.config import get_settings
from app.models.source import Source
from app.utils.url_validator import validate_external_url


class RSSConnector(Connector):
    platform = "rss"

    async def fetch(self, source: Source) -> list[dict[str, Any]]:
        settings = get_settings()
        url = validate_external_url(source.url)

        async with httpx.AsyncClient(timeout=settings.collect_timeout_seconds) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            content = response.text

        feed = feedparser.parse(content)
        items: list[dict[str, Any]] = []

        for entry in feed.entries:
            published = None
            if getattr(entry, "published_parsed", None):
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif getattr(entry, "updated_parsed", None):
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            link = getattr(entry, "link", source.url)
            entry_id = getattr(entry, "id", link)
            content_html = ""
            if entry.get("content"):
                content_html = entry.content[0].get("value", "")
            elif entry.get("summary"):
                content_html = entry.summary

            items.append(
                {
                    "external_id": f"rss:{entry_id}",
                    "platform": source.platform if source.platform != "atom" else "rss",
                    "content_type": "article",
                    "title": getattr(entry, "title", None),
                    "content_html": content_html,
                    "url": link,
                    "author_name": getattr(entry, "author", None),
                    "published_at": published,
                    "tags": [t.term for t in getattr(entry, "tags", []) if getattr(t, "term", None)],
                    "raw_data": dict(entry),
                }
            )

        return items


class AtomConnector(RSSConnector):
    platform = "atom"
