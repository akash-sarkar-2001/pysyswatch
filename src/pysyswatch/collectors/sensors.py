import logging

import psutil

from pysyswatch.core.exceptions import CollectorError
from pysyswatch.models.schemas import SensorInfo

logger = logging.getLogger(__name__)


def collect_sensors() -> list[SensorInfo]:
    """Collects hardware temperature sensors."""
    sensors: list[SensorInfo] = []

    try:
        # Check if the function exists (not available on all platforms)
        if not hasattr(psutil, "sensors_temperatures"):
            return sensors

        temps = psutil.sensors_temperatures()
        if not temps:
            logger.debug("No temperature sensors found (likely VM or container).")
            return sensors

        for name, entries in temps.items():
            for entry in entries:
                label = entry.label or name
                sensors.append(
                    SensorInfo(
                        label=label,
                        temperature=entry.current,
                        high=entry.high,
                        critical=entry.critical,
                    )
                )
        return sensors
    except Exception as e:
        logger.error(f"Failed to collect sensor metrics: {e}")
        raise CollectorError(f"Sensor collection failed: {e}")
