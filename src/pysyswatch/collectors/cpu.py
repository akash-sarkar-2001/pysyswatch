import logging
import os

import psutil

from pysyswatch.core.exceptions import CollectorError
from pysyswatch.models.schemas import CpuMetrics

logger = logging.getLogger(__name__)


def collect_cpu_metrics(interval: float = 0.1) -> CpuMetrics:
    """Collects CPU usage, core count, and load averages."""
    try:
        usage = psutil.cpu_percent(interval=interval)
        cores = psutil.cpu_count(logical=True) or 1

        try:
            load = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
        except (AttributeError, OSError):
            load = (0.0, 0.0, 0.0)

        return CpuMetrics(usage_percent=usage, core_count=cores, load_average=load)
    except Exception as e:
        logger.error(f"Failed to collect CPU metrics: {e}")
        raise CollectorError(f"CPU collection failed: {e}")
