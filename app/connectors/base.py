from abc import ABC, abstractmethod
from typing import Any

from app.models.source import Source


class Connector(ABC):
    platform: str = "generic"

    @abstractmethod
    async def fetch(self, source: Source) -> list[dict[str, Any]]: ...

    def normalize_platform(self, source: Source) -> str:
        return source.platform
