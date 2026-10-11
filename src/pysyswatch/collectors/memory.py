import logging

import psutil

from pysyswatch.core.exceptions import CollectorError
from pysyswatch.models.schemas import MemoryMetrics

logger = logging.getLogger(__name__)

BYTES_IN_GB = 1024**3


def collect_memory_metrics() -> MemoryMetrics:
    """Collects system RAM and Swap usage."""
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return MemoryMetrics(
            total_gb=round(mem.total / BYTES_IN_GB, 2),
            used_gb=round(mem.used / BYTES_IN_GB, 2),
            usage_percent=mem.percent,
            swap_total_gb=round(swap.total / BYTES_IN_GB, 2),
            swap_used_gb=round(swap.used / BYTES_IN_GB, 2),
            swap_usage_percent=swap.percent,
        )
    except Exception as e:
        logger.error(f"Failed to collect memory metrics: {e}")
        raise CollectorError(f"Memory collection failed: {e}")
