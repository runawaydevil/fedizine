from fastapi import APIRouter

from app import __author__, __author_email__, __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "fedizine",
        "version": __version__,
        "author": __author__,
        "author_email": __author_email__,
    }
