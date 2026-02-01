"""
SmartParlay FastAPI Application

Main application entry point with middleware, routing, and lifecycle management.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time
import logging

from app.core.config import settings
from app.api.routes import parlay, teams, games, players

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.

    Startup:
    - Initialize database connections
    - Warm up JAX (compile simulation kernel)
    - Load correlation matrices into Redis
    - Start background tasks

    Shutdown:
    - Close database connections
    - Flush caches
    - Stop background workers
    """
    logger.info("🚀 Starting SmartParlay application...")

    # Startup tasks
    try:
        # Initialize JAX (warm up JIT compilation)
        logger.info("Warming up JAX simulation kernel...")
        from app.services.copula import benchmark_simulation
        benchmark_results = benchmark_simulation(n_legs=3, n_sims=1000)
        logger.info(f"JAX warmup complete: {benchmark_results['jax_time_second_call_ms']:.1f}ms")

        # TODO: Initialize database connection pool
        # TODO: Load correlation matrices from disk to Redis
        # TODO: Start background odds polling worker

        logger.info("✅ Application startup complete")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield

    # Shutdown tasks
    logger.info("🛑 Shutting down SmartParlay application...")
    # TODO: Close database connections
    # TODO: Stop background workers
    logger.info("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Production-grade SGP optimizer with Student-t Copula correlation modeling",
    version=settings.api_version,
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# GZip compression for responses >1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses for monitoring."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for monitoring and debugging."""
    logger.info(f"{request.method} {request.url.path} - Client: {request.client.host}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code}")
    return response


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed messages."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to prevent 500 errors from leaking details."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request.headers.get("X-Request-ID", "unknown"),
        },
    )


# Health check endpoints
@app.get("/health", tags=["system"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.

    Returns:
        200: Service is healthy
        503: Service is unhealthy
    """
    # TODO: Add actual health checks (database, Redis, etc.)
    return {
        "status": "healthy",
        "version": settings.api_version,
        "environment": settings.app_env,
    }


@app.get("/health/ready", tags=["system"])
async def readiness_check():
    """
    Readiness check for Kubernetes/container orchestration.

    Checks:
    - Database connection
    - Redis connection
    - JAX warmup complete
    """
    checks = {
        "database": "ok",  # TODO: Actual database check
        "redis": "ok",  # TODO: Actual Redis check
        "jax": "ok",  # JAX is warmed up in lifespan
    }

    all_healthy = all(status == "ok" for status in checks.values())

    return {
        "ready": all_healthy,
        "checks": checks,
    }


@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.api_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health",
    }


# Include routers
app.include_router(parlay.router, prefix=f"/api/{settings.api_version}")
app.include_router(teams.router, prefix=f"/api/{settings.api_version}")
app.include_router(games.router, prefix=f"/api/{settings.api_version}")
app.include_router(players.router, prefix=f"/api/{settings.api_version}")


# Prometheus metrics endpoint (if enabled)
if settings.prometheus_port:
    from prometheus_client import make_asgi_app
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
