from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import get_settings
from app.editorial.copy import MONTH_NAMES
from app.models.edition import Edition

settings = get_settings()

SKIP_ISSUE_SECTIONS = frozenset({"Editorial", "Footer"})

SECTION_LABELS: dict[str, str] = {
    "Highlights": "Featured fragments",
    "Fragments": "Fragments",
    "Photos": "Photos",
    "Readings": "Readings",
    "Videos": "Videos",
    "Commented links": "Links",
    "Communities": "Communities",
    "Agenda": "Notes",
}

SECTION_INTROS: dict[str, str] = {
    "Highlights": "Selected pieces from this month's federated trail.",
    "Fragments": "Status notes, threads, and short discoveries from the Fediverse.",
    "Photos": "Images worth keeping on the shelf.",
    "Readings": "Books, articles, and longer reads.",
    "Videos": "Moving pictures from the timeline.",
    "Commented links": "Bookmarks with context.",
    "Communities": "Posts from community spaces.",
    "Agenda": "Dates and events worth noting.",
}


def make_jinja_env(*, autoescape: list[str]) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(settings.templates_dir)),
        autoescape=select_autoescape(autoescape),
    )


def attach_month_filter(env: Environment) -> None:
    env.filters["month_name"] = lambda period: (
        MONTH_NAMES.get(int(period.split("-")[1]), period)
        if "-" in period
        else period
    )


def group_edition_by_section(edition: Edition) -> dict[str, list]:
    sections: dict[str, list] = {}
    for ei in sorted(edition.edition_items, key=lambda x: (x.section, x.sort_order)):
        sections.setdefault(ei.section, []).append(ei)
    return sections


def public_issue_sections(edition: Edition) -> dict[str, list]:
    grouped = group_edition_by_section(edition)
    return {name: items for name, items in grouped.items() if name not in SKIP_ISSUE_SECTIONS and items}


def section_label(name: str) -> str:
    return SECTION_LABELS.get(name, name)


def section_intro(name: str) -> str:
    return SECTION_INTROS.get(name, "Collected from public Fediverse and RSS sources.")


def edition_stats(edition: Edition) -> tuple[int, int]:
    items = edition.edition_items or []
    source_ids = {ei.item.source_id for ei in items if ei.item and ei.item.source_id}
    return len(items), len(source_ids)


def editorial_note(edition: Edition, month: str) -> str:
    if edition.editorial_text and edition.editorial_text.strip():
        return edition.editorial_text.strip()
    return (
        f"This issue gathers selected fragments from the Fediverse: posts, links, "
        f"media, and small discoveries collected during {month}."
    )


def issue_fragment_layout(content_type: str | None) -> str:
    ct = (content_type or "status").lower()
    if ct in ("image", "album", "photo"):
        return "photo"
    if ct == "video":
        return "video"
    if ct in ("link", "article"):
        return "link"
    if ct in ("book", "review"):
        return "reading"
    return "status"


def issue_sources(edition: Edition) -> list:
    seen: set = set()
    sources = []
    for ei in edition.edition_items or []:
        source = ei.item.source if ei.item else None
        if not source or source.id in seen:
            continue
        seen.add(source.id)
        sources.append(source)
    return sorted(sources, key=lambda s: (s.platform, s.name))


def issue_toc_entries(sections: dict[str, list]) -> list[dict]:
    entries: list[dict] = [
        {"num": "01", "title": "Editorial note", "anchor": "editorial", "count": None},
    ]
    idx = 2
    for section_name, items in sections.items():
        entries.append(
            {
                "num": f"{idx:02d}",
                "title": section_label(section_name),
                "anchor": f"section-{idx}",
                "count": len(items),
            }
        )
        idx += 1
    entries.append(
        {"num": f"{idx:02d}", "title": "Colophon", "anchor": "colophon", "count": None}
    )
    return entries


def attach_issue_filters(env: Environment) -> None:
    env.filters["section_label"] = section_label
    env.filters["section_intro"] = section_intro
    env.filters["issue_layout"] = issue_fragment_layout
