import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.postgres import init_db
from app.db.qdrant import init_qdrant_collection
from app.api.routes import health, regulations, analysis, audit
from app.utils.reranking import _get_reranker

# Attach a StreamHandler directly to the "app" logger.
# basicConfig() is a no-op once uvicorn has claimed the root logger,
# so we bypass it entirely and own the "app" namespace directly.
_app_logger = logging.getLogger("app")
if not _app_logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%H:%M:%S")
    )
    _app_logger.addHandler(_handler)
_app_logger.setLevel(logging.INFO)
_app_logger.propagate = False  # prevent double-printing via uvicorn's root handler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting up Regulatory Intelligence Platform...")
    try:
        await init_db()
        logger.info("PostgreSQL tables ready")
    except Exception as e:
        logger.warning("Database not available — %s", e)
    try:
        await init_qdrant_collection()
        logger.info("Qdrant collection ready")
    except Exception as e:
        logger.warning("Qdrant not available — %s", e)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _get_reranker)
    logger.info("Reranker model loaded")

    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Regulatory Intelligence Platform",
    description="Multi-agent AI platform for Nigerian financial and compliance regulations.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(regulations.router)
app.include_router(analysis.router)
app.include_router(audit.router)