import logging
import sys

from pysyswatch.config.settings import settings


def setup_logging() -> None:
    """Configure structured application logging."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Define a clean, structured format
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
