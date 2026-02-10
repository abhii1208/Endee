from fastapi import APIRouter

from backend.app.config import get_settings
from backend.app.services.endee_client import get_endee_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    client = get_endee_client()
    description = client._index.describe()

    return {
        "app": settings.app_name,
        "environment": settings.environment,
        "endee_index": settings.endee_index_name,
        "endee_index_stats": description,
    }

