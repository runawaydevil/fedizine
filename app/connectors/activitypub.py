from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.connectors.base import Connector
from app.core.config import get_settings
from app.models.source import Source
from app.utils.url_validator import validate_external_url


class ActivityPubConnector(Connector):
    platform = "activitypub"

    async def fetch(self, source: Source) -> list[dict[str, Any]]:
        settings = get_settings()
        profile_url = validate_external_url(source.url)
        parsed = urlparse(profile_url)
        host = parsed.netloc

        async with httpx.AsyncClient(
            timeout=settings.collect_timeout_seconds,
            headers={"Accept": "application/activity+json, application/ld+json"},
        ) as client:
            actor = await self._resolve_actor(client, profile_url, host)
            outbox = actor.get("outbox")
            if not outbox:
                return []

            items: list[dict[str, Any]] = []
            next_url: str | None = outbox
            pages = 0

            while next_url and pages < 5:
                page = await self._fetch_json(client, next_url)
                # Outbox pages vary: orderedItems vs items, and next may be a URL or an object with id.
                for obj in page.get("orderedItems", page.get("items", [])):
                    if isinstance(obj, str):
                        obj = await self._fetch_json(client, obj)
                    normalized = self._normalize_activity(obj, source, host)
                    if normalized:
                        items.append(normalized)

                next_url = page.get("next")
                if isinstance(next_url, dict):
                    next_url = next_url.get("id")
                pages += 1

        return items

    async def _resolve_actor(
        self, client: httpx.AsyncClient, profile_url: str, host: str
    ) -> dict:
        if "@" in profile_url and not profile_url.endswith("/"):
            handle = profile_url.split("/")[-1].lstrip("@")
            if "@" not in handle:
                handle = f"{handle}@{host}"
            wf_url = f"https://{host}/.well-known/webfinger?resource=acct:{handle}"
            wf = await self._fetch_json(client, wf_url, accept="application/jrd+json")
            for link in wf.get("links", []):
                if link.get("rel") == "self":
                    return await self._fetch_json(client, link["href"])
        return await self._fetch_json(client, profile_url if profile_url.endswith("/") else profile_url)

    async def _fetch_json(
        self, client: httpx.AsyncClient, url: str, accept: str | None = None
    ) -> dict:
        headers = {"Accept": accept or "application/activity+json, application/ld+json"}
        response = await client.get(url, headers=headers, follow_redirects=True)
        response.raise_for_status()
        return response.json()

    def _normalize_activity(
        self, obj: dict, source: Source, host: str
    ) -> dict[str, Any] | None:
        obj_type = obj.get("type", "")
        if obj_type in ("Tombstone", "Delete"):
            return None

        allowed = {"Note", "Article", "Image", "Video", "Event", "Document"}
        if obj_type not in allowed:
            return None

        obj_id = obj.get("id", "")
        published = obj.get("published") or obj.get("created")
        published_dt = None
        if published:
            published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))

        content_html = obj.get("content") or obj.get("summary") or ""
        content_type_map = {
            "Note": "status",
            "Article": "article",
            "Image": "image",
            "Video": "video",
            "Event": "event",
            "Document": "link",
        }

        media = []
        for att in obj.get("attachment", []) or []:
            if isinstance(att, dict) and att.get("url"):
                media.append(
                    {
                        "type": att.get("mediaType", "image").split("/")[0],
                        "url": att.get("url"),
                        "alt": att.get("name"),
                    }
                )

        tags = []
        for tag in obj.get("tag", []) or []:
            if isinstance(tag, dict) and tag.get("type") == "Hashtag":
                tags.append(tag.get("name", "").lstrip("#"))

        return {
            "external_id": f"ap:{host}:{obj_id}",
            "platform": source.platform,
            "content_type": content_type_map.get(obj_type, "status"),
            "title": obj.get("name") or obj.get("summary", "")[:120] or None,
            "content_html": content_html,
            "url": obj_id,
            "author_name": None,
            "published_at": published_dt,
            "tags": tags,
            "media": media,
            "metrics": {},
            "raw_data": obj,
        }
