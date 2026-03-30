"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.core.auth.router import limiter, router as auth_router
from app.core.plugins.loader import ModuleLoader
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown."""
    # Startup
    loader = ModuleLoader()
    loader.discover_modules()
    loader.load_modules(app)

    yield

    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="DentalPin API",
    description="Open source dental clinic management software",
    version="0.1.0",
    lifespan=lifespan,
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
    allowed_origins.extend(["http://localhost:3000", "http://127.0.0.1:3000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    if settings.ENVIRONMENT == "development":
        return JSONResponse(
            status_code=500,
            content={
                "data": None,
                "message": str(exc),
                "errors": [str(exc)],
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "data": None,
            "message": "Internal server error",
            "errors": [],
        },
    )


# Mount auth router
app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/api/v1")
async def api_root() -> dict:
    """API root endpoint."""
    return {
        "message": "DentalPin API",
        "version": "0.1.0",
        "docs": "/docs" if settings.ENVIRONMENT == "development" else None,
    }
