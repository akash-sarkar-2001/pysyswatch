import logging
import subprocess

from pysyswatch.core.exceptions import CollectorError, ServiceUnavailableError
from pysyswatch.models.schemas import ServiceInfo

logger = logging.getLogger(__name__)


def is_systemd_running() -> bool:
    try:
        # Check if systemd is PID 1 or active in the environment
        result = subprocess.run(
            ["systemctl", "is-system-running"],
            capture_output=True,
            text=True,
            check=False,
        )
        # Even if the system is degraded, systemctl works.
        # Only 'offline' or a missing binary indicates unavailability.
        return result.returncode != 127 and "offline" not in result.stdout
    except FileNotFoundError:
        return False


def collect_services() -> list[ServiceInfo]:
    """Collects systemd services and their current states."""
    if not is_systemd_running():
        logger.warning("systemd is not running or unavailable in this environment.")
        raise ServiceUnavailableError("systemd is not available")

    services: list[ServiceInfo] = []

    try:
        result = subprocess.run(
            [
                "systemctl",
                "list-units",
                "--type=service",
                "--all",
                "--no-pager",
                "--no-legend",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        for line in result.stdout.splitlines():
            parts = line.split(maxsplit=4)
            if len(parts) >= 4:
                services.append(
                    ServiceInfo(
                        name=parts[0].replace(".service", ""),
                        load_state=parts[1],
                        active_state=parts[2],
                        sub_state=parts[3],
                        description=parts[4] if len(parts) == 5 else "",
                    )
                )
        return services
    except subprocess.CalledProcessError as e:
        logger.error(f"systemctl command failed: {e.stderr}")
        raise CollectorError(f"Failed to query systemd: {e}")
    except Exception as e:
        logger.error(f"Unexpected error collecting services: {e}")
        raise CollectorError(f"Service collection failed: {e}")
