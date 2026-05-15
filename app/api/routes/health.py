from fastapi import APIRouter
from app.models.responses import HealthResponse

router = APIRouter(prefix="/health", tags=['health'])

@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="0.1.0",
        services={
            "postgres": "not connected yet",
            "qdrant": "not connected yet",
            "redis": "not connected yet"
        },
    )
