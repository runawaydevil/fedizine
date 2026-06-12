import uuid
from datetime import datetime

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.deps import CurrentUser, DbSession, OptionalUser
from app.core.security import verify_password
from app.models.item import Item
from app.models.user import User
from app.schemas.source import SourceCreate
from app.services.edition_service import (
    build_edition,
    get_edition_with_items,
    get_or_create_edition,
    update_item_status,
)
from app.services.publish_service import build_pdf, publish_edition
from app.services.scoring_service import score_user_items
from app.services.source_service import create_source, delete_source, list_sources
from app.web.templates import templates
from app.workers.tasks import collect_source

router = APIRouter(prefix="/desk", tags=["desk"])
settings = get_settings()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user: OptionalUser):
    if user:
        return RedirectResponse("/desk/", status_code=303)
    return templates.TemplateResponse(
        request, "admin/login.html", {"app_name": settings.app_name}
    )


@router.post("/login")
def login_submit(
    request: Request,
    db: DbSession,
    email: str = Form(...),
    password: str = Form(...),
):
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "admin/login.html",
            {"app_name": settings.app_name, "error": "Incorrect email or password."},
            status_code=401,
        )
    request.session["user_id"] = str(user.id)
    return RedirectResponse("/desk/", status_code=303)


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/desk/login", status_code=303)


@router.get("/", response_class=HTMLResponse)
def desk_home(request: Request, db: DbSession, user: CurrentUser):
    now = datetime.now()
    period = now.strftime("%Y-%m")
    edition = get_or_create_edition(db, user.id, period)

    total_items = db.scalar(
        select(func.count()).select_from(Item).where(Item.user_id == user.id)
    ) or 0
    selected = db.scalar(
        select(func.count())
        .select_from(Item)
        .where(Item.user_id == user.id, Item.status.in_(("selected", "featured")))
    ) or 0
    featured = db.scalar(
        select(func.count())
        .select_from(Item)
        .where(Item.user_id == user.id, Item.status == "featured")
    ) or 0

    return templates.TemplateResponse(
        request,
        "admin/desk.html",
        {
            "user": user,
            "edition": edition,
            "total_items": total_items,
            "selected": selected,
            "featured": featured,
            "app_name": settings.app_name,
        },
    )


@router.get("/sources", response_class=HTMLResponse)
def sources_list(request: Request, db: DbSession, user: CurrentUser):
    sources = list_sources(db, user.id)
    return templates.TemplateResponse(
        request,
        "admin/sources.html",
        {"user": user, "sources": sources, "app_name": settings.app_name},
    )


@router.post("/sources")
def sources_create(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    name: str = Form(...),
    platform: str = Form(...),
    source_type: str = Form("feed"),
    url: str = Form(...),
    handle: str = Form(""),
):
    try:
        create_source(
            db,
            user.id,
            SourceCreate(
                name=name,
                platform=platform,
                source_type=source_type,
                url=url,
                handle=handle or None,
            ),
        )
    except ValueError as exc:
        sources = list_sources(db, user.id)
        return templates.TemplateResponse(
            request,
            "admin/sources.html",
            {
                "user": user,
                "sources": sources,
                "error": str(exc),
                "app_name": settings.app_name,
            },
            status_code=400,
        )
    return RedirectResponse("/desk/sources", status_code=303)


@router.post("/sources/{source_id}/collect")
def sources_collect(source_id: uuid.UUID, user: CurrentUser):
    collect_source.delay(str(source_id))
    return RedirectResponse("/desk/fragments", status_code=303)


@router.post("/sources/{source_id}/delete")
def sources_delete(source_id: uuid.UUID, db: DbSession, user: CurrentUser):
    delete_source(db, user.id, source_id)
    return RedirectResponse("/desk/sources", status_code=303)


@router.get("/fragments", response_class=HTMLResponse)
def fragments_list(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    status: str = "candidate",
):
    query = select(Item).where(Item.user_id == user.id)
    if status != "all":
        query = query.where(Item.status == status)
    items = list(
        db.scalars(query.order_by(Item.score.desc(), Item.published_at.desc()).limit(100)).all()
    )
    return templates.TemplateResponse(
        request,
        "admin/fragments.html",
        {
            "user": user,
            "items": items,
            "current_status": status,
            "app_name": settings.app_name,
        },
    )


@router.post("/fragments/{item_id}/action")
def fragment_action(
    item_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    action: str = Form(...),
):
    status_map = {
        "include": "selected",
        "ignore": "ignored",
        "feature": "featured",
    }
    new_status = status_map.get(action)
    if new_status:
        update_item_status(db, user.id, item_id, new_status)
    return RedirectResponse("/desk/fragments", status_code=303)


@router.post("/fragments/{item_id}/edit")
def fragment_edit(
    item_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
    title: str = Form(""),
    summary: str = Form(""),
):
    item = db.scalar(select(Item).where(Item.id == item_id, Item.user_id == user.id))
    if item:
        if title:
            item.title = title
        if summary:
            item.summary = summary
        db.commit()
    return RedirectResponse("/desk/fragments", status_code=303)


@router.get("/issues", response_class=HTMLResponse)
def issues_view(request: Request, db: DbSession, user: CurrentUser):
    period = datetime.now().strftime("%Y-%m")
    edition = get_or_create_edition(db, user.id, period)
    edition = get_edition_with_items(db, edition.id)
    return templates.TemplateResponse(
        request,
        "admin/issues.html",
        {"user": user, "edition": edition, "app_name": settings.app_name},
    )


@router.post("/issues/build")
def issues_build(db: DbSession, user: CurrentUser):
    period = datetime.now().strftime("%Y-%m")
    edition = get_or_create_edition(db, user.id, period)
    score_user_items(db, user.id, period)
    build_edition(db, edition)
    return RedirectResponse("/desk/issues", status_code=303)


@router.get("/proof", response_class=HTMLResponse)
def proof_view(request: Request, db: DbSession, user: CurrentUser):
    period = datetime.now().strftime("%Y-%m")
    edition = get_or_create_edition(db, user.id, period)
    edition = get_edition_with_items(db, edition.id)
    return templates.TemplateResponse(
        request,
        "admin/proof.html",
        {
            "user": user,
            "edition": edition,
            "app_name": settings.app_name,
            "public_url": settings.app_public_url,
        },
    )


@router.post("/proof/generate-pdf")
def proof_generate_pdf(db: DbSession, user: CurrentUser):
    period = datetime.now().strftime("%Y-%m")
    edition = get_or_create_edition(db, user.id, period)
    build_pdf(db, edition)
    return RedirectResponse("/desk/proof", status_code=303)


@router.post("/proof/publish")
def proof_publish(db: DbSession, user: CurrentUser):
    period = datetime.now().strftime("%Y-%m")
    edition = get_or_create_edition(db, user.id, period)
    edition = get_edition_with_items(db, edition.id)
    if not edition.edition_items:
        raise HTTPException(400, "This issue needs at least one fragment.")
    publish_edition(db, edition)
    return RedirectResponse(f"/{period}/", status_code=303)
