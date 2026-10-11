FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create a dedicated non-root user/group
RUN groupadd -r pysyswatch && useradd -r -g pysyswatch pysyswatch

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/

# Install the application (SQLite is built into Python)
RUN pip install .

RUN chown -R pysyswatch:pysyswatch /app

USER pysyswatch
EXPOSE 8001

# Native Python health check to avoid requiring curl
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/healthz')" || exit 1

CMD ["uvicorn", "pysyswatch.api.app:app", "--host", "0.0.0.0", "--port", "8001"]