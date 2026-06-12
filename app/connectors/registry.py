from pathlib import Path

import yaml

from app.connectors.activitypub import ActivityPubConnector
from app.connectors.base import Connector
from app.connectors.rss import AtomConnector, RSSConnector

_CONNECTORS: dict[str, type[Connector]] = {
    "rss": RSSConnector,
    "atom": AtomConnector,
    "activitypub": ActivityPubConnector,
    "mastodon": ActivityPubConnector,
    "pixelfed": ActivityPubConnector,
    "lemmy": ActivityPubConnector,
    "peertube": ActivityPubConnector,
    "bookwyrm": ActivityPubConnector,
    "writefreely": ActivityPubConnector,
    "gotosocial": ActivityPubConnector,
    "misskey": ActivityPubConnector,
}


def get_connector(platform: str) -> Connector:
    registry = _load_registry()
    platform_info = registry.get("platforms", {}).get(platform, {})
    connector_name = platform_info.get("connector", platform)

    cls = _CONNECTORS.get(connector_name) or _CONNECTORS.get(platform)
    if not cls:
        return ActivityPubConnector()
    return cls()


def _load_registry() -> dict:
    path = Path(__file__).resolve().parent.parent.parent / "config" / "platform_registry.yml"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}
