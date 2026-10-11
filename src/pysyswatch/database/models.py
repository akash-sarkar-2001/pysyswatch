from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, BigInteger
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )

    # Core Metrics
    cpu_usage = Column(Float, nullable=False)
    load_average_1m = Column(Float, nullable=False)

    memory_usage = Column(Float, nullable=False)

    # Storing the maximum disk partition usage for trending
    disk_usage_max = Column(Float, nullable=False)

    # Network I/O totals at time of collection
    network_rx_bytes = Column(BigInteger, nullable=False)
    network_tx_bytes = Column(BigInteger, nullable=False)

    # Snapshot of the deterministic health state
    health_state = Column(String(20), nullable=False)
