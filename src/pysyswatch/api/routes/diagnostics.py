import asyncio

from fastapi import APIRouter, Depends, HTTPException

from pysyswatch.api.deps import verify_api_key
from pysyswatch.collectors.cpu import collect_cpu_metrics
from pysyswatch.collectors.disk import collect_disk_metrics
from pysyswatch.collectors.memory import collect_memory_metrics
from pysyswatch.core.exceptions import CollectorError
from pysyswatch.diagnostics.engine import evaluate_system_health
from pysyswatch.models.schemas import HealthDiagnosis, SystemStatus

router = APIRouter(dependencies=[Depends(verify_api_key)], tags=["Diagnostics"])


@router.get("/status", response_model=SystemStatus)
async def get_system_status() -> SystemStatus:
    try:
        cpu, mem, disk = await asyncio.gather(
            asyncio.to_thread(collect_cpu_metrics),
            asyncio.to_thread(collect_memory_metrics),
            asyncio.to_thread(collect_disk_metrics)
        )
        
        try:
            from pysyswatch.collectors.services import collect_services
            svcs = await asyncio.to_thread(collect_services)
        except Exception:
            svcs = None
            
        try:
            from pysyswatch.collectors.network import collect_network_metrics
            net = await asyncio.to_thread(collect_network_metrics)
        except Exception:
            net = None

        health = evaluate_system_health(cpu=cpu, memory=mem, disk=disk, services=svcs, network=net)

        return SystemStatus(cpu=cpu, memory=mem, disk=disk, health=health)
    except CollectorError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to collect system status: {e}"
        )


@router.get("/health", response_model=HealthDiagnosis)
async def get_health_only() -> HealthDiagnosis:
    """Returns only the deterministic health state and identified issues."""
    try:
        cpu, mem, disk = await asyncio.gather(
            asyncio.to_thread(collect_cpu_metrics),
            asyncio.to_thread(collect_memory_metrics),
            asyncio.to_thread(collect_disk_metrics),
        )
        try:
            from pysyswatch.collectors.services import collect_services
            svcs = await asyncio.to_thread(collect_services)
        except Exception:
            svcs = None
            
        try:
            from pysyswatch.collectors.network import collect_network_metrics
            net = await asyncio.to_thread(collect_network_metrics)
        except Exception:
            net = None
            
        return evaluate_system_health(cpu=cpu, memory=mem, disk=disk, services=svcs, network=net)
    except CollectorError as e:
        raise HTTPException(status_code=500, detail=f"Health evaluation failed: {e}")
