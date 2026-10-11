import logging

import psutil

from pysyswatch.core.exceptions import CollectorError
from pysyswatch.models.schemas import DiskMetrics, DiskPartitionMetrics

logger = logging.getLogger(__name__)

BYTES_IN_GB = 1024**3


def collect_disk_metrics() -> DiskMetrics:
    """Collects usage metrics for all physical disk partitions."""
    try:
        partitions_data: list[DiskPartitionMetrics] = []
        # all=False ensures we only get physical partitions
        partitions = psutil.disk_partitions(all=False)

        for part in partitions:
            # Skip read-only or inaccessible partitions gracefully
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions_data.append(
                    DiskPartitionMetrics(
                        device=part.device,
                        mountpoint=part.mountpoint,
                        fstype=part.fstype,
                        total_gb=round(usage.total / BYTES_IN_GB, 2),
                        used_gb=round(usage.used / BYTES_IN_GB, 2),
                        free_gb=round(usage.free / BYTES_IN_GB, 2),
                        usage_percent=usage.percent,
                    )
                )
            except PermissionError:
                logger.debug(f"Permission denied accessing disk {part.mountpoint}")
                continue
            except OSError as e:
                logger.debug(f"OS error accessing disk {part.mountpoint}: {e}")
                continue

        return DiskMetrics(partitions=partitions_data)
    except Exception as e:
        logger.error(f"Failed to collect disk metrics: {e}")
        raise CollectorError(f"Disk collection failed: {e}")
