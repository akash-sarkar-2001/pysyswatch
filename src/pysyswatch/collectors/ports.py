import logging

import psutil

from pysyswatch.core.exceptions import CollectorError
from pysyswatch.models.schemas import PortInfo

logger = logging.getLogger(__name__)


def collect_listening_ports() -> list[PortInfo]:
    """Collects all listening TCP/UDP ports and their associated processes."""
    ports: list[PortInfo] = []

    try:
        # Requires elevated privileges to see PIDs owned by other users
        connections = psutil.net_connections(kind="inet")

        for conn in connections:
            if conn.status == "LISTEN" and conn.laddr:
                pid = conn.pid
                process_name = None

                if pid:
                    try:
                        proc = psutil.Process(pid)
                        process_name = proc.name()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_name = "restricted"

                protocol = (
                    "TCP" if conn.type == 1 else "UDP" if conn.type == 2 else "UNKNOWN"
                )

                ports.append(
                    PortInfo(
                        port=conn.laddr.port,
                        protocol=protocol,
                        address=conn.laddr.ip,
                        pid=pid,
                        process_name=process_name,
                    )
                )

        # Sort by port number
        return sorted(ports, key=lambda p: p.port)
    except psutil.AccessDenied:
        logger.warning(
            "Access denied when reading network connections. Run as root for full visibility."
        )
        raise CollectorError(
            "Permission denied: Cannot read network connections. Try running with sudo."
        )
    except Exception as e:
        logger.error(f"Failed to collect port metrics: {e}")
        raise CollectorError(f"Port collection failed: {e}")
