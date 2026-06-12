from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import get_settings
from app.web import admin, health, public

settings = get_settings()

for path in (settings.storage_path, settings.public_path, settings.media_path):
    Path(path).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

if settings.trust_proxy:
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.app_secret_key,
    max_age=settings.session_max_age,
    same_site="lax",
    https_only=settings.is_production,
)

static_dir = settings.static_dir
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

assets_dir = settings.assets_dir
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    icon = settings.assets_dir / "favicon.ico"
    if icon.exists():
        return FileResponse(icon, media_type="image/x-icon")
    raise HTTPException(404)

public_storage = Path(settings.public_path)
if public_storage.exists():
    app.mount("/files", StaticFiles(directory=str(public_storage)), name="files")

app.include_router(health.router)
app.include_router(public.router)
app.include_router(admin.router)
