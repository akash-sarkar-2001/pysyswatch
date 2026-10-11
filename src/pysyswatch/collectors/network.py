import logging
import socket

import psutil

from pysyswatch.core.exceptions import CollectorError
from pysyswatch.models.schemas import NetworkInterface, NetworkMetrics

logger = logging.getLogger(__name__)


def collect_network_metrics() -> NetworkMetrics:
    """Collects network interfaces, IP addresses, and I/O statistics."""
    try:
        if_addrs = psutil.net_if_addrs()
        if_stats = psutil.net_if_stats()
        io_counters = psutil.net_io_counters(pernic=True)

        interfaces: dict[str, NetworkInterface] = {}

        for iface_name, addrs in if_addrs.items():
            ipv4: list[str] = []
            ipv6: list[str] = []
            mac: str | None = None

            for addr in addrs:
                if addr.family == socket.AF_INET:
                    ipv4.append(addr.address)
                elif addr.family == socket.AF_INET6:
                    ipv6.append(addr.address)
                elif addr.family == getattr(psutil, "AF_LINK", -1):
                    mac = addr.address

            stats = if_stats.get(iface_name)
            counters = io_counters.get(iface_name)

            interfaces[iface_name] = NetworkInterface(
                name=iface_name,
                is_up=stats.isup if stats else False,
                mac_address=mac,
                ipv4_addresses=ipv4,
                ipv6_addresses=ipv6,
                rx_bytes=counters.bytes_recv if counters else 0,
                tx_bytes=counters.bytes_sent if counters else 0,
                rx_dropped=counters.dropin if counters else 0,
                tx_dropped=counters.dropout if counters else 0,
                rx_errors=counters.errin if counters else 0,
                tx_errors=counters.errout if counters else 0,
            )

        return NetworkMetrics(interfaces=interfaces)
    except Exception as e:
        logger.error(f"Failed to collect network metrics: {e}")
        raise CollectorError(f"Network collection failed: {e}")
