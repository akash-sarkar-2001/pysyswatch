import secrets
import time
from collections.abc import Generator

from fastapi import HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session

from pysyswatch.config.settings import settings
from pysyswatch.database.engine import get_db

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Simple in-memory rate limiter
# Dictionary mapping IP string to a list of timestamps
_rate_limit_records: dict[str, list[float]] = {}

def check_rate_limit(request: Request) -> None:
    """Enforces a basic sliding-window rate limit per IP address."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Initialize or clean up old timestamps
    timestamps = _rate_limit_records.get(client_ip, [])
    timestamps = [t for t in timestamps if now - t < 60]
    
    if len(timestamps) >= settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Too Many Requests")
        
    timestamps.append(now)
    _rate_limit_records[client_ip] = timestamps


async def verify_api_key(request: Request, api_key: str = Security(api_key_header)) -> None:
    """Validates the API key if one is configured in the environment."""
    check_rate_limit(request)
    
    # Fail closed: protected endpoints must never become public because a
    # deployment forgot to configure its key.
    configured_key = settings.api_key
    if not configured_key or configured_key == "your-secure-api-key-here":
        raise HTTPException(
            status_code=503,
            detail="API authentication is not configured",
        )
    if not api_key or not secrets.compare_digest(api_key, configured_key):
        raise HTTPException(
            status_code=403, detail="Forbidden: Invalid or missing API Key"
        )


def get_database_session() -> Generator[Session, None, None]:
    """Yields a database session and ensures it is closed after the request."""
    yield from get_db()
