"""
ECCRP Custom Middleware
Rate limiting, audit logging, request ID injection.
"""

import time
import uuid
from collections import defaultdict
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter. Use Redis-backed in production."""

    def __init__(self, app: ASGIApp, requests_per_minute: int = 120):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._counters: dict = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip health checks
        if request.url.path in ("/health", "/readiness"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - 60

        # Clean old entries
        self._counters[client_ip] = [
            t for t in self._counters[client_ip] if t > window_start
        ]

        if len(self._counters[client_ip]) >= self.requests_per_minute:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry after 60 seconds."},
                headers={"Retry-After": "60"},
            )

        self._counters[client_ip].append(now)
        return await call_next(request)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log all mutating API calls for audit trail."""

    AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    SKIP_PATHS = {"/health", "/readiness", "/api/v1/docs", "/api/v1/openapi.json"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method not in self.AUDIT_METHODS or request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Async audit write (fire-and-forget via background task in real impl)
        logger.info(
            "api_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=latency_ms,
            request_id=getattr(request.state, "request_id", None),
            ip=request.client.host if request.client else None,
        )
        return response
