import logging

import psutil

from pysyswatch.core.exceptions import CollectorError
from pysyswatch.models.schemas import ProcessInfo

logger = logging.getLogger(__name__)

BYTES_IN_MB = 1024**2


def collect_processes(sort_by: str = "cpu", limit: int = 20) -> list[ProcessInfo]:
    """Collects system processes, sorted and limited."""
    processes: list[ProcessInfo] = []

    try:
        # We need a brief sleep for psutil to accurately calculate CPU percent per process
        # Using a context manager ensures we capture it across all processes simultaneously
        # Initialize cpu_percent for all processes first (non-blocking)
        procs = list(psutil.process_iter(["pid", "name", "username", "status", "create_time"]))
        for proc in procs:
            try:
                proc.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Wait once for the whole system
        import time
        time.sleep(0.1)

        for proc in procs:
            try:
                cpu_pct = proc.cpu_percent(interval=None)
                mem_info = proc.memory_info()
                mem_pct = proc.memory_percent()

                processes.append(
                    ProcessInfo(
                        pid=proc.info["pid"],
                        name=proc.info["name"] or "unknown",
                        cpu_percent=round(cpu_pct, 1),
                        memory_percent=round(mem_pct, 1),
                        memory_rss_mb=round(mem_info.rss / BYTES_IN_MB, 2),
                        username=proc.info["username"] or "unknown",
                        status=proc.info["status"] or "unknown",
                        create_time=proc.info["create_time"] or 0.0,
                    )
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        # Sort logic
        if sort_by == "memory":
            processes.sort(key=lambda p: p.memory_rss_mb, reverse=True)
        else:  # default to cpu
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)

        return processes[:limit]
    except Exception as e:
        logger.error(f"Failed to collect process metrics: {e}")
        raise CollectorError(f"Process collection failed: {e}")
