"""
Election Compliance & Candidate Readiness Platform (ECCRP)
Main FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine, Base
from app.api.v1.router import api_router
from app.core.middleware import (
    RateLimitMiddleware,
    AuditLogMiddleware,
    RequestIdMiddleware,
)

setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting ECCRP platform", version=settings.APP_VERSION)
    # Startup: create tables if not exists (handled by Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")
    yield
    logger.info("Shutting down ECCRP platform")


app = FastAPI(
    title="Election Compliance & Candidate Readiness Platform",
    description="""
    ECCRP is a production-grade SaaS platform that converts Indian election law
    into actionable compliance workflows for candidates, parties, lawyers,
    consultants, journalists, and governance professionals.
    
    Supports: Lok Sabha, Rajya Sabha, State Legislative Assemblies & Councils,
    Gram Panchayat, Mandal Parishad, Zilla Parishad, Municipality, Municipal Corporation.
    """,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(RequestIdMiddleware)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(api_router, prefix=settings.API_V1_STR)


# ── Health & Root ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    return {
        "platform": "Election Compliance & Candidate Readiness Platform (ECCRP)",
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": f"{settings.API_V1_STR}/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/readiness", tags=["Health"])
async def readiness_check():
    """Deep readiness check — verifies DB, Redis, and OpenSearch connectivity."""
    from app.core.health import check_all_services
    results = await check_all_services()
    status_code = 200 if all(r["status"] == "ok" for r in results.values()) else 503
    return JSONResponse(content=results, status_code=status_code)
