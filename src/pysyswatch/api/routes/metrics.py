import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query

from pysyswatch.api.deps import verify_api_key
from pysyswatch.collectors.cpu import collect_cpu_metrics
from pysyswatch.collectors.disk import collect_disk_metrics
from pysyswatch.collectors.memory import collect_memory_metrics
from pysyswatch.collectors.network import collect_network_metrics
from pysyswatch.collectors.processes import collect_processes
from pysyswatch.collectors.services import collect_services
from pysyswatch.core.exceptions import CollectorError, ServiceUnavailableError
from pysyswatch.models.schemas import (
    CpuMetrics,
    DiskMetrics,
    MemoryMetrics,
    NetworkMetrics,
    ProcessInfo,
    ServiceInfo,
)

router = APIRouter(dependencies=[Depends(verify_api_key)], tags=["Metrics"])


@router.get("/cpu", response_model=CpuMetrics)
async def get_cpu() -> CpuMetrics:
    try:
        return await asyncio.to_thread(collect_cpu_metrics)
    except CollectorError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory", response_model=MemoryMetrics)
async def get_memory() -> MemoryMetrics:
    try:
        return await asyncio.to_thread(collect_memory_metrics)
    except CollectorError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disk", response_model=DiskMetrics)
async def get_disk() -> DiskMetrics:
    try:
        return await asyncio.to_thread(collect_disk_metrics)
    except CollectorError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/network", response_model=NetworkMetrics)
async def get_network() -> NetworkMetrics:
    try:
        return await asyncio.to_thread(collect_network_metrics)
    except CollectorError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processes", response_model=list[ProcessInfo])
async def get_processes(
    sort: str = "cpu", limit: int = Query(default=20, ge=1, le=200)
) -> list[ProcessInfo]:
    if sort not in ["cpu", "memory"]:
        raise HTTPException(status_code=400, detail="Sort must be 'cpu' or 'memory'")
    try:
        return await asyncio.to_thread(collect_processes, sort_by=sort, limit=limit)
    except CollectorError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services", response_model=list[ServiceInfo])
async def get_services() -> list[ServiceInfo]:
    try:
        return await asyncio.to_thread(collect_services)
    except ServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except CollectorError as e:
        raise HTTPException(status_code=500, detail=str(e))
