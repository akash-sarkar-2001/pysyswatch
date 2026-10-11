import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from pysyswatch import __version__
from pysyswatch.api.routes import diagnostics, metrics
from pysyswatch.core.exceptions import PySysWatchError

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PySysWatch API",
    description="Production-Grade Linux System Monitoring & Diagnostics API",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

from pysyswatch.config.settings import settings

# Allow CORS for configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["X-API-Key"],
)


# Global Exception Handler for custom application errors
@app.exception_handler(PySysWatchError)
async def pysyswatch_exception_handler(
    request: Request, exc: PySysWatchError
) -> JSONResponse:
    logger.error(f"API Error at {request.url.path}: {exc!s}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal system monitoring error occurred.",
            "type": type(exc).__name__,
        },
    )


# Include Routers
app.include_router(metrics.router, prefix="/api/v1/metrics")
app.include_router(diagnostics.router, prefix="/api/v1")


@app.get("/healthz", tags=["System"])
async def liveness_probe() -> dict[str, str]:
    """Lightweight endpoint for Docker/Kubernetes liveness probes."""
    return {"status": "ok", "version": __version__}


from fastapi.responses import JSONResponse, RedirectResponse


@app.get("/", include_in_schema=False)
def redirect_root() -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def serve_dashboard() -> str:
    """Serves the professional static dashboard."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    try:
        with open(dashboard_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Dashboard file not found. Ensure dashboard.html is deployed."
