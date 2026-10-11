import pytest
from unittest.mock import patch, MagicMock
from pysyswatch.collectors.cpu import collect_cpu_metrics
from pysyswatch.collectors.memory import collect_memory_metrics
from pysyswatch.core.exceptions import CollectorError

@patch("pysyswatch.collectors.cpu.psutil.cpu_percent")
@patch("pysyswatch.collectors.cpu.psutil.cpu_count")
@patch("pysyswatch.collectors.cpu.os.getloadavg")
def test_collect_cpu_metrics(mock_getloadavg: MagicMock, mock_cpu_count: MagicMock, mock_cpu_percent: MagicMock) -> None:
    """Ensure CPU metrics are formatted correctly from psutil data."""
    mock_cpu_percent.return_value = 35.5
    mock_cpu_count.return_value = 8
    mock_getloadavg.return_value = (1.5, 1.2, 1.0)
    
    metrics = collect_cpu_metrics()
    
    assert metrics.usage_percent == 35.5
    assert metrics.core_count == 8
    assert metrics.load_average == (1.5, 1.2, 1.0)
    mock_cpu_percent.assert_called_once()

@patch("pysyswatch.collectors.cpu.psutil.cpu_percent")
def test_collect_cpu_metrics_error(mock_cpu_percent: MagicMock) -> None:
    """Ensure unexpected OS exceptions are caught and re-raised as CollectorErrors."""
    mock_cpu_percent.side_effect = Exception("Mocked OS Failure")
    
    with pytest.raises(CollectorError) as exc:
        collect_cpu_metrics()
        
    assert "CPU collection failed" in str(exc.value)

@patch("pysyswatch.collectors.memory.psutil.virtual_memory")
@patch("pysyswatch.collectors.memory.psutil.swap_memory")
def test_collect_memory_metrics(mock_swap: MagicMock, mock_virtual: MagicMock) -> None:
    """Ensure memory byte-to-GB conversion math is accurate."""
    # Mock namedtuples returned by psutil
    mock_virtual.return_value = MagicMock(total=17179869184, used=8589934592, percent=50.0) # 16GB total, 8GB used
    mock_swap.return_value = MagicMock(total=4294967296, used=0, percent=0.0) # 4GB total, 0GB used
    
    metrics = collect_memory_metrics()
    
    assert metrics.total_gb == 16.0
    assert metrics.used_gb == 8.0
    assert metrics.usage_percent == 50.0
    assert metrics.swap_total_gb == 4.0
    assert metrics.swap_used_gb == 0.0