import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from pysyswatch.database.models import SystemMetric
from pysyswatch.models.schemas import (
    CpuMetrics,
    DiskMetrics,
    HealthDiagnosis,
    MemoryMetrics,
    NetworkMetrics,
)

logger = logging.getLogger(__name__)


def save_system_snapshot(
    db: Session,
    cpu: CpuMetrics,
    memory: MemoryMetrics,
    disk: DiskMetrics,
    network: NetworkMetrics | None,
    health: HealthDiagnosis,
) -> None:
    """Transforms and persists a system metric snapshot to the database."""
    try:
        # Aggregate disk metrics to track the most constrained partition
        max_disk = max((p.usage_percent for p in disk.partitions), default=0.0)

        # Aggregate total network I/O across all active interfaces
        total_rx = (
            sum(i.rx_bytes for i in network.interfaces.values()) if network else 0
        )
        total_tx = (
            sum(i.tx_bytes for i in network.interfaces.values()) if network else 0
        )

        metric_record = SystemMetric(
            cpu_usage=cpu.usage_percent,
            load_average_1m=cpu.load_average[0],
            memory_usage=memory.usage_percent,
            disk_usage_max=max_disk,
            network_rx_bytes=total_rx,
            network_tx_bytes=total_tx,
            health_state=health.state.value,
        )

        db.add(metric_record)
        db.commit()
        logger.debug("System metrics snapshot persisted successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist metrics snapshot: {e}")


def prune_old_metrics(db: Session, retention_days: int) -> int:
    """Deletes system metrics older than the retention policy."""
    try:
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        # SQLAlchemy 2.0 delete syntax
        timestamp_column: Any = SystemMetric.timestamp
        deleted_count = (
            db.query(SystemMetric).filter(timestamp_column < cutoff).delete()
        )
        db.commit()
        if deleted_count > 0:
            logger.info(
                f"Pruned {deleted_count} historical metric records older than {retention_days} days."
            )
        return deleted_count
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to prune old metrics: {e}")
        return 0
