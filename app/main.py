import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.postgres import init_db
from app.db.qdrant import init_qdrant_collection
from app.api.routes import regulations, audit, analysis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Regulatory Intelligence Platform...")
    await init_db()
    logger.info("PostgreSQL tables ready")
    await init_qdrant_collection()
    logger.info("Qdrant collection ready")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Regulatory Intelligence Platform",
    description="Agentic AI platform for Nigerian financial compliance",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(regulations.router)
app.include_router(audit.router)
app.include_router(analysis.router)


@app.get("/health")
async def health():
    return {"status": "ok"}