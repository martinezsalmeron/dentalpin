"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth.router import limiter
from app.core.auth.router import router as auth_router
from app.core.plugins.loader import load_modules
from app.core.plugins.processor import PendingProcessor
from app.core.plugins.service import ModuleService
from app.core.scheduler import init_scheduler, shutdown_scheduler
from app.core.schemas import ErrorResponse
from app.database import async_session_maker, engine, get_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    load_modules(app)

    # Sync in-memory registry into core_module (best-effort).
    try:
        async with async_session_maker() as session:
            await ModuleService(session).reconcile_with_db()
    except Exception:
        logger.exception("Module registry reconciliation failed at startup")

    # Process pending install/uninstall/upgrade operations.
    try:
        processor = PendingProcessor(async_session_maker)
        processed = await processor.run()
        if processed:
            logger.info("Processed pending module operations: %s", processed)
    except Exception:
        logger.exception("Pending module processor raised")

    # Initialize scheduler for background jobs
    init_scheduler()

    yield

    # Shutdown
    shutdown_scheduler()
    await engine.dispose()


app = FastAPI(
    title="DentalPin API",
    description="Open source dental clinic management software",
    version="2.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configure CORS
allowed_origins = settings.allowed_origins_list.copy()
if settings.ENVIRONMENT == "development":
    allowed_origins.extend(
        [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _cors_headers(request: Request) -> dict[str, str]:
    # CORSMiddleware can't add headers to responses produced by exception
    # handlers (BaseHTTPMiddleware-based stacks lose the response when an
    # exception escapes). Without these headers, browsers report any 5xx
    # as a network error ("can't connect to server") instead of surfacing
    # the real status — which masks bugs and confuses users. So we mirror
    # CORSMiddleware's allow-list logic here for error responses.
    origin = request.headers.get("origin")
    if not origin:
        return {}
    if origin in allowed_origins or "*" in allowed_origins:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Vary": "Origin",
        }
    return {}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for HTTP exceptions using standard ErrorResponse format."""
    error_response = ErrorResponse(
        message=str(exc.detail),
        errors=[str(exc.detail)] if exc.detail else [],
    )
    headers = dict(exc.headers or {})
    headers.update(_cors_headers(request))
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
        headers=headers,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.exception("Unhandled exception", exc_info=exc)
    if settings.ENVIRONMENT == "development":
        error_response = ErrorResponse(
            message=str(exc),
            errors=[str(exc)],
        )
    else:
        error_response = ErrorResponse(
            message="Internal server error",
            errors=[],
        )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
        headers=_cors_headers(request),
    )


# Mount auth router
app.include_router(auth_router, prefix="/api/v1")

# Mount module management router (install/uninstall/upgrade/restart).
from app.core.plugins.router import router as modules_router  # noqa: E402

app.include_router(modules_router, prefix="/api/v1")

# Mount AI agents infrastructure router (approval queue, audit, agent CRUD).
from app.core.agents.router import router as agents_router  # noqa: E402

app.include_router(agents_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> JSONResponse:
    """Liveness probe — process is up.

    Used by the proxy/orchestrator to decide whether the container should
    receive traffic. Must NOT depend on the DB: a transient DB blip should
    not pull the backend out of the load balancer (we used to do that and
    Cloudflare ended up serving "no available server" until someone redeployed
    by hand).
    """
    return JSONResponse(content={"status": "healthy", "version": "2.0.0"})


@app.get("/health/ready")
async def readiness_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """Readiness probe — schema is reachable.

    Probes a core table so monitoring catches the case where the DB volume
    gets recreated under a running container (schema gone, every business
    endpoint 500s). Recovery from that state belongs in the entrypoint
    (`alembic upgrade heads`) plus an explicit container restart — not in
    the proxy healthcheck, since Docker's `restart: unless-stopped` does
    not auto-restart on healthcheck failure.
    """
    try:
        await db.execute(text("SELECT 1 FROM users LIMIT 1"))
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={"status": "unready", "version": "2.0.0", "error": str(exc)},
        )
    return JSONResponse(content={"status": "ready", "version": "2.0.0"})


@app.get("/api/v1")
async def api_root() -> dict:
    """API root endpoint."""
    return {
        "message": "DentalPin API",
        "version": "2.0.0",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else None,
    }
