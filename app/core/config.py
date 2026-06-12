from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

def _resolve_base_dir() -> Path:
    package_root = Path(__file__).resolve().parent.parent.parent
    if (package_root / "templates").exists():
        return package_root
    docker_root = Path("/app")
    if (docker_root / "templates").exists():
        return docker_root
    return package_root


BASE_DIR = _resolve_base_dir()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Fedizine"
    app_env: str = "development"
    app_port: int = 8000
    host_port: int = 4927
    app_public_url: str = "https://zine.murad.social"
    app_secret_key: str = "change-me"
    trust_proxy: bool = True

    default_locale: str = "en_US"
    default_timezone: str = "America/Sao_Paulo"

    database_url: str = "postgresql+psycopg://fedizine:change-me@localhost:5432/fedizine"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    storage_path: str = "/data/storage"
    public_path: str = "/data/public"
    media_path: str = "/data/media"
    max_media_size_mb: int = 10

    default_user_email: str = "pablo@zine.murad.social"
    default_user_name: str = "Pablo Murad"
    default_user_slug: str = "pablo"

    enable_public_signup: bool = False
    session_max_age: int = 86400

    editorial_score_threshold: int = 50
    collection_interval_hours: int = 24
    collect_timeout_seconds: int = 30

    enable_ai_assistant: bool = False
    ai_provider: str = "none"
    openai_api_key: str = ""

    allowed_url_schemes: str = "https"
    block_private_ips: bool = True

    templates_dir: Path = BASE_DIR / "templates"
    static_dir: Path = BASE_DIR / "static"
    assets_dir: Path = BASE_DIR / "assets"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
