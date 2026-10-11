from pysyswatch.diagnostics.engine import evaluate_system_health
from pysyswatch.models.schemas import (
    CpuMetrics,
    DiskMetrics,
    DiskPartitionMetrics,
    HealthState,
    MemoryMetrics,
    NetworkInterface,
    NetworkMetrics,
)


def test_evaluate_system_health_healthy() -> None:
    """Verify that normal metrics yield a HEALTHY state."""
    cpu = CpuMetrics(usage_percent=45.0, core_count=4, load_average=(1.0, 1.0, 1.0))
    mem = MemoryMetrics(
        total_gb=16.0,
        used_gb=4.0,
        usage_percent=25.0,
        swap_total_gb=2.0,
        swap_used_gb=0.0,
        swap_usage_percent=0.0,
    )
    disk = DiskMetrics(
        partitions=[
            DiskPartitionMetrics(
                device="/dev/sda1",
                mountpoint="/",
                fstype="ext4",
                total_gb=100.0,
                used_gb=40.0,
                free_gb=60.0,
                usage_percent=40.0,
            )
        ]
    )

    health = evaluate_system_health(cpu=cpu, memory=mem, disk=disk)

    assert health.state == HealthState.HEALTHY
    assert len(health.issues) == 0


def test_evaluate_system_health_critical_cpu() -> None:
    """Verify that exceeding the critical CPU threshold forces a CRITICAL state."""
    cpu = CpuMetrics(usage_percent=99.0, core_count=4, load_average=(4.5, 4.0, 3.5))
    mem = MemoryMetrics(
        total_gb=16.0,
        used_gb=4.0,
        usage_percent=25.0,
        swap_total_gb=2.0,
        swap_used_gb=0.0,
        swap_usage_percent=0.0,
    )
    disk = DiskMetrics(partitions=[])

    health = evaluate_system_health(cpu=cpu, memory=mem, disk=disk)

    assert health.state == HealthState.CRITICAL
    assert any("CPU" in issue for issue in health.issues)


def test_evaluate_system_health_network_down() -> None:
    """Verify that an unexpected down interface triggers a WARNING."""
    cpu = CpuMetrics(usage_percent=10.0, core_count=4, load_average=(0.1, 0.1, 0.1))
    mem = MemoryMetrics(
        total_gb=16.0,
        used_gb=4.0,
        usage_percent=25.0,
        swap_total_gb=2.0,
        swap_used_gb=0.0,
        swap_usage_percent=0.0,
    )
    disk = DiskMetrics(partitions=[])
    network = NetworkMetrics(
        interfaces={
            "eth0": NetworkInterface(name="eth0", is_up=False, rx_bytes=0, tx_bytes=0)
        }
    )

    health = evaluate_system_health(cpu=cpu, memory=mem, disk=disk, network=network)

    assert health.state == HealthState.WARNING
    assert any("eth0" in issue for issue in health.issues)
