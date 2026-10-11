from pysyswatch.config.settings import settings
from pysyswatch.models.schemas import (
    CpuMetrics,
    DiskMetrics,
    HealthDiagnosis,
    HealthState,
    MemoryMetrics,
    NetworkMetrics,
    ServiceInfo,
)


def evaluate_system_health(
    cpu: CpuMetrics,
    memory: MemoryMetrics,
    disk: DiskMetrics,
    services: list[ServiceInfo] | None = None,
    network: NetworkMetrics | None = None,
) -> HealthDiagnosis:
    """Evaluates multiple system metrics to determine overall system health."""
    issues: list[str] = []
    state = HealthState.HEALTHY

    # Evaluate CPU
    if cpu.usage_percent >= settings.cpu_critical_threshold:
        issues.append(f"CRITICAL: CPU usage is at {cpu.usage_percent}%")
        state = HealthState.CRITICAL
    elif cpu.usage_percent >= settings.cpu_warning_threshold:
        issues.append(f"WARNING: CPU usage is at {cpu.usage_percent}%")
        if state != HealthState.CRITICAL:
            state = HealthState.WARNING

    # Evaluate Memory
    if memory.usage_percent >= settings.memory_critical_threshold:
        issues.append(f"CRITICAL: Memory usage is at {memory.usage_percent}%")
        state = HealthState.CRITICAL
    elif memory.usage_percent >= settings.memory_warning_threshold:
        issues.append(f"WARNING: Memory usage is at {memory.usage_percent}%")
        if state != HealthState.CRITICAL:
            state = HealthState.WARNING

    # Evaluate Disk
    for partition in disk.partitions:
        if partition.usage_percent >= settings.disk_critical_threshold:
            issues.append(
                f"CRITICAL: Disk '{partition.mountpoint}' is at {partition.usage_percent}% capacity"
            )
            state = HealthState.CRITICAL
        elif partition.usage_percent >= settings.disk_warning_threshold:
            issues.append(
                f"WARNING: Disk '{partition.mountpoint}' is at {partition.usage_percent}% capacity"
            )
            if state != HealthState.CRITICAL:
                state = HealthState.WARNING

    # Evaluate Services (if available)
    if services:
        failed_services = [
            s.name
            for s in services
            if s.active_state == "failed" or s.sub_state == "failed"
        ]
        if failed_services:
            issues.append(
                f"WARNING: {len(failed_services)} systemd services have failed ({', '.join(failed_services[:3])}{'...' if len(failed_services) > 3 else ''})"
            )
            if state != HealthState.CRITICAL:
                state = HealthState.WARNING

    # Evaluate Network (if available)
    if network:
        ignore_prefixes = ("lo", "docker", "veth", "br-", "tailscale", "tun", "tap", "wg", "Local Area Connection")
        for name, iface in network.interfaces.items():
            if not iface.is_up and not name.startswith(ignore_prefixes):
                issues.append(
                    f"WARNING: Network interface '{name}' is DOWN unexpectedly."
                )
                if state != HealthState.CRITICAL:
                    state = HealthState.WARNING

    return HealthDiagnosis(state=state, issues=issues)
