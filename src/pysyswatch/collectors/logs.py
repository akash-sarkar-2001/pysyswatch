import logging
import subprocess

from pysyswatch.collectors.services import is_systemd_running
from pysyswatch.core.exceptions import CollectorError, ServiceUnavailableError
from pysyswatch.models.schemas import LogEntry

logger = logging.getLogger(__name__)


def collect_logs(
    lines: int = 50, level: str = "err", service: str | None = None
) -> list[LogEntry]:
    """Collects recent system logs via journalctl."""
    if not is_systemd_running():
        raise ServiceUnavailableError(
            "journald requires systemd, which is not available."
        )

    logs: list[LogEntry] = []

    cmd = [
        "journalctl",
        "--no-pager",
        "--output=short-iso",
        f"--lines={lines}",
        f"--priority={level}",
    ]

    if service:
        cmd.extend(["--unit", service])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        for line in result.stdout.splitlines():
            # Basic parsing of journalctl short-iso output
            # Format: 2026-09-23T21:55:47+05:30 hostname service[pid]: message
            parts = line.split(" ", 3)
            if len(parts) >= 4:
                logs.append(
                    LogEntry(
                        timestamp=parts[0],
                        level=level.upper(),
                        service=parts[2]
                        .split("[")[0]
                        .replace(":", ""),  # Clean up PID/colon
                        message=parts[3],
                    )
                )
        return logs
    except subprocess.CalledProcessError as e:
        logger.error(f"journalctl failed: {e.stderr}")
        raise CollectorError(
            "Failed to read system logs. Ensure user is in 'systemd-journal' or 'adm' group."
        )
    except Exception as e:
        logger.error(f"Unexpected error collecting logs: {e}")
        raise CollectorError(f"Log collection failed: {e}")
