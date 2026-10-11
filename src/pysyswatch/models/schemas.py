from enum import Enum

from pydantic import BaseModel


class HealthState(str, Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class CpuMetrics(BaseModel):
    usage_percent: float
    core_count: int
    load_average: tuple[float, float, float]


class MemoryMetrics(BaseModel):
    total_gb: float
    used_gb: float
    usage_percent: float
    swap_total_gb: float
    swap_used_gb: float
    swap_usage_percent: float


class DiskPartitionMetrics(BaseModel):
    device: str
    mountpoint: str
    fstype: str
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float


class DiskMetrics(BaseModel):
    partitions: list[DiskPartitionMetrics]


class HealthDiagnosis(BaseModel):
    state: HealthState
    issues: list[str]


class SystemStatus(BaseModel):
    cpu: CpuMetrics
    memory: MemoryMetrics
    disk: DiskMetrics
    health: HealthDiagnosis


class NetworkInterface(BaseModel):
    name: str
    is_up: bool
    mac_address: str | None = None
    ipv4_addresses: list[str] = []
    ipv6_addresses: list[str] = []
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_dropped: int = 0
    tx_dropped: int = 0
    rx_errors: int = 0
    tx_errors: int = 0


class NetworkMetrics(BaseModel):
    interfaces: dict[str, NetworkInterface]


class ProcessInfo(BaseModel):
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_rss_mb: float
    username: str
    status: str
    create_time: float


class ServiceInfo(BaseModel):
    name: str
    description: str
    load_state: str
    active_state: str
    sub_state: str


class PortInfo(BaseModel):
    port: int
    protocol: str
    address: str
    pid: int | None = None
    process_name: str | None = None


class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    message: str


class SensorInfo(BaseModel):
    label: str
    temperature: float
    high: float | None = None
    critical: float | None = None
