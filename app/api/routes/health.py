from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.postgres import get_db_session
from app.db.qdrant import get_qdrant_client
from app.models.responses import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db_session),
) -> HealthResponse:
    # PostgreSQL
    postgres_status = "unavailable"
    try:
        await db.execute(text("SELECT 1"))
        postgres_status = "connected"
    except Exception:
        pass

    # Qdrant
    qdrant_status = "unavailable"
    try:
        client = await get_qdrant_client()
        await client.collection_exists(settings.qdrant_collection_name)
        qdrant_status = "connected"
    except Exception:
        pass

    all_ok = postgres_status == "connected" and qdrant_status == "connected"

    return HealthResponse(
        status="ok" if all_ok else "degraded",
        version="0.1.0",
        services={
            "postgres": postgres_status,
            "qdrant": qdrant_status,
            "redis": "not configured",
        },
    )
