import logging
import signal
import time
from typing import Any

from pysyswatch.collectors.cpu import collect_cpu_metrics
from pysyswatch.collectors.disk import collect_disk_metrics
from pysyswatch.collectors.memory import collect_memory_metrics
from pysyswatch.collectors.services import collect_services
from pysyswatch.core.exceptions import ServiceUnavailableError
from pysyswatch.collectors.network import collect_network_metrics
from pysyswatch.config.settings import settings
from pysyswatch.core.exceptions import CollectorError
from pysyswatch.database.engine import SessionLocal, init_db
from pysyswatch.database.repositories.metrics import save_system_snapshot
from pysyswatch.diagnostics.engine import evaluate_system_health
from pysyswatch.services.notifier import send_alert_if_needed
from pysyswatch.database.repositories.metrics import prune_old_metrics
from pysyswatch.models.schemas import HealthState

logger = logging.getLogger(__name__)


class BackgroundMonitor:
    """A resilient daemon that polls system metrics and persists them."""

    def __init__(self) -> None:
        self._running = False
        self.interval = settings.collection_interval
        self._last_health_state = HealthState.HEALTHY
        self._tick_count = 0

        # Register signal handlers for graceful shutdown (systemctl stop)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum: int, frame: Any) -> None:
        logger.info(f"Received shutdown signal ({signum}). Terminating gracefully...")
        self._running = False

    def start(self) -> None:
        logger.info(
            f"Starting PySysWatch background monitor (Interval: {self.interval}s)"
        )

        # Ensure database is initialized before starting the loop
        init_db()
        self._running = True

        while self._running:
            self._tick()

            # Sleep in small increments to remain responsive to shutdown signals
            for _ in range(self.interval * 10):
                if not self._running:
                    break
                time.sleep(0.1)

        logger.info("Background monitor stopped successfully.")

    def _tick(self) -> None:
        """Executes a single collection and persistence cycle."""
        try:
            # Collect metrics with individual fallbacks to prevent cascading failures
            try:
                cpu = collect_cpu_metrics()
            except CollectorError:
                logger.warning("Skipping cycle due to CPU collection failure.")
                return

            try:
                mem = collect_memory_metrics()
            except CollectorError:
                logger.warning("Skipping cycle due to Memory collection failure.")
                return

            try:
                disk = collect_disk_metrics()
            except CollectorError:
                logger.warning("Skipping cycle due to Disk collection failure.")
                return

            try:
                net = collect_network_metrics()
            except CollectorError:
                net = None  # Tolerate missing network data

            # Evaluate overall health
            try:
                svcs = collect_services()
            except Exception:
                svcs = None
            health = evaluate_system_health(cpu=cpu, memory=mem, disk=disk, network=net, services=svcs)

            # 1. Trigger Webhook Alert if state degraded
            send_alert_if_needed(health, self._last_health_state)
            self._last_health_state = health.state

            # Log warnings/critical issues emitted by the engine
            if health.issues:
                for issue in health.issues:
                    logger.warning(f"Diagnostic Issue: {issue}")

            # Persist to database
            with SessionLocal() as db:
                save_system_snapshot(
                    db=db, cpu=cpu, memory=mem, disk=disk, network=net, health=health
                )
                
                # 3. Prune old data once per hour (assuming 10s interval = 360 ticks)
                self._tick_count += 1
                if self._tick_count >= 360:
                    prune_old_metrics(db, settings.metrics_retention_days)
                    self._tick_count = 0

        except Exception:
            logger.exception("Unexpected error during monitor tick")
