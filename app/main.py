from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.postgres import init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Starting Regulatory Intelligence Platform...")
    await init_db()
    yield
    print("Shutting down...")


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

from app.api.routes import health, regulations, analysis, audit

app.include_router(health.router)
app.include_router(regulations.router)
app.include_router(analysis.router)
app.include_router(audit.router)