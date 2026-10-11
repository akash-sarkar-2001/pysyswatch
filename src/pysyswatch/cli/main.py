import time

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table

import pysyswatch
from pysyswatch.collectors.cpu import collect_cpu_metrics
from pysyswatch.collectors.disk import collect_disk_metrics
from pysyswatch.collectors.logs import collect_logs
from pysyswatch.collectors.memory import collect_memory_metrics
from pysyswatch.collectors.network import collect_network_metrics
from pysyswatch.collectors.ports import collect_listening_ports
from pysyswatch.collectors.processes import collect_processes
from pysyswatch.collectors.sensors import collect_sensors
from pysyswatch.collectors.services import collect_services
from pysyswatch.core.exceptions import CollectorError, ServiceUnavailableError
from pysyswatch.diagnostics.engine import evaluate_system_health
from pysyswatch.models.schemas import HealthState
from pysyswatch.services.monitor import BackgroundMonitor

app = typer.Typer(
    help="""
    PySysWatch - Advanced System Monitoring & Diagnostics.
    
    A comprehensive toolkit for local and remote system observability. 
    
    Quick Start (Local):
      - run `pysyswatch status` for a quick health check
      - run `pysyswatch top` for a live terminal monitor
      - run `pysyswatch dashboard` to start the web UI
      
    Docker Deployment (Recommended for Background Daemon):
      1. Copy environment variables: `cp .env.example .env` (Add an API key)
      2. Build and start containers: `docker-compose up -d --build`
      3. The API and Dashboard will be available at http://localhost:8001
      4. The Background Daemon will run seamlessly as a service
      5. To view container logs, run: `docker-compose logs -f`
    """,
    no_args_is_help=True,
)
console = Console()


@app.command()
def dashboard(
    port: int = typer.Option(8001, "--port", "-p", help="Port to run the dashboard on"),
    host: str = typer.Option(
        "127.0.0.1", "--host", "-h", help="Host to bind the API to"
    ),
) -> None:
    """Start the REST API and professional web dashboard."""
    import uvicorn

    console.print(
        f"[bold green]Starting PySysWatch Dashboard at http://{host}:{port}/dashboard[/bold green]"
    )
    try:
        uvicorn.run("pysyswatch.api.app:app", host=host, port=port, log_level="info")
    except Exception as e:
        console.print(f"[bold red]Failed to start dashboard:[/bold red] {e}")
        raise typer.Exit(1)


def version_callback(value: bool) -> None:
    if value:
        console.print(
            f"PySysWatch version: [bold cyan]{pysyswatch.__version__}[/bold cyan]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show application version.",
    ),
) -> None:
    pass


@app.command()
def cpu(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Display CPU usage and load average."""
    try:
        metrics = collect_cpu_metrics()

        if json_output:
            typer.echo(metrics.model_dump_json(indent=2))
            return

        table = Table(title="CPU Metrics", show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_row("Core Count", str(metrics.core_count))
        table.add_row("Usage", f"{metrics.usage_percent}%")
        table.add_row(
            "Load Average (1/5/15m)",
            f"{metrics.load_average[0]:.2f} / {metrics.load_average[1]:.2f} / {metrics.load_average[2]:.2f}",
        )

        console.print(table)
    except CollectorError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def memory(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Display Memory and Swap usage."""
    try:
        metrics = collect_memory_metrics()

        if json_output:
            typer.echo(metrics.model_dump_json(indent=2))
            return

        table = Table(title="Memory & Swap Metrics", show_header=False)
        table.add_column("Type", style="cyan")
        table.add_column("Usage", style="magenta")
        table.add_column("Total", style="green")
        table.add_column("Percent", style="yellow")

        table.add_row(
            "RAM",
            f"{metrics.used_gb} GB",
            f"{metrics.total_gb} GB",
            f"{metrics.usage_percent}%",
        )
        table.add_row(
            "Swap",
            f"{metrics.swap_used_gb} GB",
            f"{metrics.swap_total_gb} GB",
            f"{metrics.swap_usage_percent}%",
        )

        console.print(table)
    except CollectorError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def disk(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    threshold: float = typer.Option(
        0.0, "--threshold", help="Only show partitions above this usage percentage"
    ),
) -> None:
    """Display physical disk partition usage."""
    try:
        metrics = collect_disk_metrics()

        if json_output:
            typer.echo(metrics.model_dump_json(indent=2))
            return

        table = Table(title="Disk Usage")
        table.add_column("Filesystem", style="cyan")
        table.add_column("Mount", style="magenta")
        table.add_column("Size", justify="right")
        table.add_column("Used", justify="right")
        table.add_column("Avail", justify="right")
        table.add_column("Use%", justify="right")

        for p in metrics.partitions:
            if p.usage_percent >= threshold:
                color = (
                    "red"
                    if p.usage_percent >= 90
                    else "yellow"
                    if p.usage_percent >= 80
                    else "green"
                )
                table.add_row(
                    p.device,
                    p.mountpoint,
                    f"{p.total_gb} GB",
                    f"{p.used_gb} GB",
                    f"{p.free_gb} GB",
                    f"[{color}]{p.usage_percent}%[/{color}]",
                )

        console.print(table)
    except CollectorError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def network(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Display network interface status and I/O statistics."""
    try:
        metrics = collect_network_metrics()

        if json_output:
            typer.echo(metrics.model_dump_json(indent=2))
            return

        table = Table(title="Network Interfaces")
        table.add_column("Interface", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("IPv4", style="green")
        table.add_column("RX (MB)", justify="right")
        table.add_column("TX (MB)", justify="right")

        for name, iface in metrics.interfaces.items():
            status_color = "green" if iface.is_up else "red"
            status_text = "UP" if iface.is_up else "DOWN"
            ipv4 = iface.ipv4_addresses[0] if iface.ipv4_addresses else "-"
            rx_mb = round(iface.rx_bytes / (1024 * 1024), 2)
            tx_mb = round(iface.tx_bytes / (1024 * 1024), 2)

            table.add_row(
                name,
                f"[{status_color}]{status_text}[/{status_color}]",
                ipv4,
                str(rx_mb),
                str(tx_mb),
            )

        console.print(table)
    except CollectorError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def processes(
    sort: str = typer.Option("cpu", "--sort", help="Sort by 'cpu' or 'memory'"),
    limit: int = typer.Option(20, "--limit", help="Number of processes to display"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Display running processes with CPU and Memory utilization."""
    if sort not in ["cpu", "memory"]:
        console.print("[bold red]Error:[/bold red] Sort must be 'cpu' or 'memory'")
        raise typer.Exit(1)

    try:
        procs = collect_processes(sort_by=sort, limit=limit)

        if json_output:
            import json

            typer.echo(json.dumps([p.model_dump() for p in procs], indent=2))
            return

        table = Table(title=f"Top {limit} Processes (Sorted by {sort.upper()})")
        table.add_column("PID", style="cyan", justify="right")
        table.add_column("User", style="magenta")
        table.add_column("Process Name", style="green")
        table.add_column("CPU %", justify="right")
        table.add_column("Mem %", justify="right")
        table.add_column("RSS (MB)", justify="right")
        table.add_column("Status")

        for p in procs:
            table.add_row(
                str(p.pid),
                p.username,
                p.name,
                str(p.cpu_percent),
                str(p.memory_percent),
                str(p.memory_rss_mb),
                p.status,
            )

        console.print(table)
    except CollectorError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def services(
    failed_only: bool = typer.Option(
        False, "--failed", help="Only show failed services"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Display systemd services status."""
    try:
        svcs = collect_services()

        if failed_only:
            svcs = [
                s for s in svcs if s.active_state == "failed" or s.sub_state == "failed"
            ]

        if json_output:
            import json

            typer.echo(json.dumps([s.model_dump() for s in svcs], indent=2))
            return

        table = Table(title="Systemd Services")
        table.add_column("Service", style="cyan")
        table.add_column("Active", style="bold")
        table.add_column("Sub", style="bold")
        table.add_column("Description")

        for s in svcs:
            active_color = (
                "red"
                if s.active_state == "failed"
                else "green"
                if s.active_state == "active"
                else "white"
            )
            sub_color = "red" if s.sub_state == "failed" else "white"

            table.add_row(
                s.name,
                f"[{active_color}]{s.active_state}[/{active_color}]",
                f"[{sub_color}]{s.sub_state}[/{sub_color}]",
                s.description[:50] + "..."
                if len(s.description) > 50
                else s.description,
            )

        console.print(table)
    except ServiceUnavailableError:
        console.print(
            "[yellow]Warning:[/yellow] systemd is not available on this system."
        )
    except CollectorError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def ports(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Display listening TCP/UDP ports and associated processes."""
    try:
        ports = collect_listening_ports()

        if json_output:
            import json

            typer.echo(json.dumps([p.model_dump() for p in ports], indent=2))
            return

        table = Table(title="Listening Ports")
        table.add_column("Port", style="cyan", justify="right")
        table.add_column("Protocol", style="magenta")
        table.add_column("Address", style="green")
        table.add_column("PID", justify="right")
        table.add_column("Process")

        for p in ports:
            table.add_row(
                str(p.port),
                p.protocol,
                p.address,
                str(p.pid) if p.pid else "-",
                p.process_name if p.process_name else "Unknown",
            )

        console.print(table)
    except CollectorError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def sensors(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Display hardware temperature sensors."""
    try:
        sensors = collect_sensors()

        if not sensors:
            console.print(
                "[yellow]No temperature sensors detected in this environment.[/yellow]"
            )
            return

        if json_output:
            import json

            typer.echo(json.dumps([s.model_dump() for s in sensors], indent=2))
            return

        table = Table(title="Hardware Temperatures")
        table.add_column("Sensor", style="cyan")
        table.add_column("Current (°C)", style="magenta", justify="right")
        table.add_column("High (°C)", justify="right")
        table.add_column("Critical (°C)", style="red", justify="right")

        for s in sensors:
            table.add_row(
                s.label,
                f"{s.temperature}°C",
                f"{s.high}°C" if s.high else "-",
                f"{s.critical}°C" if s.critical else "-",
            )

        console.print(table)
    except CollectorError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def logs(
    lines: int = typer.Option(20, "--lines", help="Number of lines to return"),
    level: str = typer.Option(
        "err", "--level", help="Log level (e.g., info, warning, err)"
    ),
    service: str = typer.Option(
        None, "--service", help="Filter by systemd service unit"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Display recent system logs from systemd journal."""
    try:
        logs = collect_logs(lines=lines, level=level, service=service)

        if json_output:
            import json

            typer.echo(json.dumps([l.model_dump() for l in logs], indent=2))
            return

        table = Table(title=f"System Logs ({level.upper()})")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Service", style="magenta")
        table.add_column("Message")

        for log in logs:
            table.add_row(
                log.timestamp,
                log.service,
                log.message[:80] + "..." if len(log.message) > 80 else log.message,
            )

        console.print(table)
    except ServiceUnavailableError:
        console.print("[yellow]Warning:[/yellow] systemd journal is not available.")
    except CollectorError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def diagnose(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Run full system diagnostics and evaluate health score."""
    try:
        cpu = collect_cpu_metrics()
        mem = collect_memory_metrics()
        disk = collect_disk_metrics()

        # Safely attempt to collect services and network
        try:
            services = collect_services()
        except (CollectorError, ServiceUnavailableError):
            services = None

        try:
            network = collect_network_metrics()
        except CollectorError:
            network = None

        diagnosis = evaluate_system_health(
            cpu=cpu, memory=mem, disk=disk, services=services, network=network
        )

        if json_output:
            typer.echo(diagnosis.model_dump_json(indent=2))
            return

        # Rich CLI Output
        health_color = (
            "green"
            if diagnosis.state == HealthState.HEALTHY
            else "yellow"
            if diagnosis.state == HealthState.WARNING
            else "red"
        )

        console.print(
            f"\n[bold]Overall Health:[/bold] [{health_color}]{diagnosis.state.value}[/{health_color}]\n"
        )

        if diagnosis.issues:
            console.print("[bold]Identified Issues:[/bold]")
            for issue in diagnosis.issues:
                issue_color = (
                    "red"
                    if issue.startswith("CRITICAL")
                    else "yellow"
                    if issue.startswith("WARNING")
                    else "white"
                )
                console.print(f"  - [{issue_color}]{issue}[/{issue_color}]")
        else:
            console.print(
                "  [green]✓ No issues detected. System is operating normally.[/green]"
            )

        console.print()

    except CollectorError as e:
        console.print(f"[bold red]Error running diagnostics:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def daemon() -> None:
    """Start the background monitoring daemon."""
    try:
        monitor = BackgroundMonitor()
        monitor.start()
    except Exception as e:
        console.print(f"[bold red]Daemon crashed:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def status(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Display overall system status and health."""
    try:
        from pysyswatch.diagnostics.engine import evaluate_system_health
        from pysyswatch.models.schemas import SystemStatus

        cpu = collect_cpu_metrics()
        mem = collect_memory_metrics()
        disk = collect_disk_metrics()

        try:
            services = collect_services()
        except Exception:
            services = None

        try:
            network = collect_network_metrics()
        except Exception:
            network = None

        health = evaluate_system_health(
            cpu=cpu, memory=mem, disk=disk, services=services, network=network
        )

        if json_output:
            status_data = SystemStatus(cpu=cpu, memory=mem, disk=disk, health=health)
            typer.echo(status_data.model_dump_json(indent=2))
            return

        table = Table(title="PySysWatch System Status", show_header=False)
        table.add_column("Metric", style="cyan", width=15)
        table.add_column("Value", style="magenta")

        table.add_section()
        table.add_row("CPU Usage", f"{cpu.usage_percent}%")
        table.add_row(
            "CPU Load",
            f"{cpu.load_average[0]:.2f} / {cpu.load_average[1]:.2f} / {cpu.load_average[2]:.2f}",
        )

        table.add_section()
        table.add_row("Memory Usage", f"{mem.usage_percent}%")
        table.add_row("Memory Used", f"{mem.used_gb} GB / {mem.total_gb} GB")

        table.add_section()
        health_color = (
            "green"
            if health.state == "HEALTHY"
            else "yellow"
            if health.state == "WARNING"
            else "red"
        )
        table.add_row(
            "Health Status", f"[{health_color}]{health.state.value}[/{health_color}]"
        )

        for issue in health.issues:
            table.add_row(" -> Issue", f"[red]{issue}[/red]")

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


def generate_status_table() -> Table:
    """Helper function to generate the status table dynamically."""
    from pysyswatch.diagnostics.engine import evaluate_system_health

    cpu = collect_cpu_metrics()
    mem = collect_memory_metrics()
    disk = collect_disk_metrics()
    try:
        services = collect_services()
    except Exception:
        services = None

    try:
        network = collect_network_metrics()
    except Exception:
        network = None

    health = evaluate_system_health(
        cpu=cpu, memory=mem, disk=disk, services=services, network=network
    )

    table = Table(title="PySysWatch Live Status", show_header=False, width=60)
    table.add_column("Metric", style="cyan", width=20)
    table.add_column("Value", style="magenta")

    table.add_section()
    table.add_row("CPU Usage", f"{cpu.usage_percent}%")
    table.add_row(
        "CPU Load",
        f"{cpu.load_average[0]:.2f} / {cpu.load_average[1]:.2f} / {cpu.load_average[2]:.2f}",
    )

    table.add_section()
    table.add_row("Memory Usage", f"{mem.usage_percent}%")
    table.add_row("Memory Used", f"{mem.used_gb} GB / {mem.total_gb} GB")

    table.add_section()
    health_color = (
        "green"
        if health.state == "HEALTHY"
        else "yellow"
        if health.state == "WARNING"
        else "red"
    )
    table.add_row(
        "Health Status", f"[{health_color}]{health.state.value}[/{health_color}]"
    )

    for issue in health.issues:
        table.add_row(" -> Issue", f"[red]{issue}[/red]")

    return table


@app.command()
def top(
    refresh: int = typer.Option(2, "--refresh", help="Refresh interval in seconds"),
) -> None:
    """Start a live-updating terminal dashboard."""
    try:
        # Use Rich's Live view to clear and redraw the table seamlessly
        with Live(
            generate_status_table(), refresh_per_second=1 / refresh, screen=True
        ) as live:
            while True:
                time.sleep(refresh)
                live.update(generate_status_table())
    except KeyboardInterrupt:
        console.print("\n[green]Exiting PySysWatch Live Mode.[/green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)
