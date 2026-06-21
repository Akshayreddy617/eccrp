"""
ECCRP Health Check Service
Verifies connectivity to all critical dependencies.
"""

import asyncio
import aioredis
from sqlalchemy import text
import structlog

from app.core.config import settings
from app.db.session import engine

logger = structlog.get_logger(__name__)


async def check_database() -> dict:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "service": "postgresql"}
    except Exception as e:
        return {"status": "error", "service": "postgresql", "detail": str(e)}


async def check_redis() -> dict:
    try:
        redis = aioredis.from_url(settings.REDIS_URL, socket_timeout=2)
        await redis.ping()
        await redis.close()
        return {"status": "ok", "service": "redis"}
    except Exception as e:
        return {"status": "error", "service": "redis", "detail": str(e)}


async def check_opensearch() -> dict:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{settings.OPENSEARCH_URL}/_cluster/health")
        if resp.status_code == 200:
            return {"status": "ok", "service": "opensearch", "detail": resp.json().get("status")}
        return {"status": "error", "service": "opensearch", "detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "error", "service": "opensearch", "detail": str(e)}


async def check_all_services() -> dict:
    results = await asyncio.gather(
        check_database(),
        check_redis(),
        check_opensearch(),
        return_exceptions=True,
    )
    return {r["service"]: r for r in results if isinstance(r, dict)}
