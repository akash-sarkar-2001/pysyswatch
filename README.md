# PySysWatch

[![CI](https://github.com/akash-sarkar-2001/pysyswatch/actions/workflows/ci.yml/badge.svg)](https://github.com/akash-sarkar-2001/pysyswatch/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**PySysWatch** is a production-grade, modular Linux system monitoring and diagnostics framework. Built with modern Python (3.12+), it provides a polished CLI, a FastAPI-powered REST API with a live web dashboard, a background telemetry daemon, and deterministic health evaluation — all deployable in seconds via Docker.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
  - [Docker (Recommended)](#docker-recommended)
  - [Local Python Package](#local-python-package)
  - [systemd Service](#systemd-service)
- [Configuration](#configuration)
- [CLI Reference](#cli-reference)
- [REST API](#rest-api)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Feature | Description |
|---|---|
| **CPU Metrics** | Usage %, core count, load averages (1/5/15m) |
| **Memory & Swap** | RAM and swap utilization in GB and percent |
| **Disk Usage** | Per-partition breakdown with configurable thresholds |
| **Network I/O** | Interface status, IPv4 addresses, RX/TX byte counters |
| **Processes** | Top processes sorted by CPU or memory, with RSS |
| **Ports** | Listening TCP/UDP ports mapped to owning processes |
| **systemd Services** | Active state and sub-state, with failed-only filter |
| **System Logs** | Filtered systemd journal entries by level and unit |
| **Hardware Sensors** | Temperature readings with high/critical thresholds |
| **Diagnostic Engine** | Deterministic `HEALTHY` / `WARNING` / `CRITICAL` evaluation |
| **Live Terminal UI** | `top`-like live-updating Rich dashboard |
| **REST API** | Async FastAPI with OpenAPI docs and optional API key auth |
| **Web Dashboard** | Browser-based live metrics dashboard at `/dashboard` |
| **Background Daemon** | Persistent telemetry daemon with SQLite/PostgreSQL storage |

---

## Architecture

```
src/pysyswatch/
├── collectors/       # Data-collection modules (cpu, disk, memory, network, …)
├── diagnostics/      # Health evaluation engine
├── analyzers/        # Post-collection analysis helpers
├── models/           # Pydantic schemas shared across layers
├── api/              # FastAPI application, routes, and schemas
│   ├── routes/       # /metrics and /diagnostics endpoint groups
│   └── dashboard.html
├── cli/              # Typer CLI commands
├── services/         # Background monitor service
├── database/         # SQLAlchemy models and Alembic migrations
└── config/           # Pydantic-Settings configuration
```

Each collector is fully independent: it gathers data, returns a typed Pydantic model, and raises `CollectorError` on failure — never crashing the caller.

---

## Quick Start

```bash
# Docker (zero-dependency)
cp .env.example .env          # add an API key
docker compose up -d --build

# Open the web dashboard
open http://localhost:8001/dashboard
```

```bash
# Or install locally and use the CLI
pip install .
pysyswatch status              # one-shot health snapshot
pysyswatch top                 # live terminal dashboard
pysyswatch diagnose            # full diagnostic report
```

---

## Installation

### Docker (Recommended)

Docker is the recommended deployment method. It runs two containers:

- **`api`** — FastAPI server + web dashboard on port `8001`
- **`daemon`** — background monitoring daemon with host-level visibility (`pid: host`, `/proc` mounted read-only)

```bash
# 1. Clone the repository
git clone https://github.com/akash-sarkar-2001/pysyswatch.git
cd pysyswatch

# 2. Configure environment
cp .env.example .env
# Edit .env and set a strong PYSYSWATCH_API_KEY

# 3. Build and start
docker compose up -d --build

# 4. View logs
docker compose logs -f

# 5. Stop
docker compose down
```

The API and dashboard are available at **http://localhost:8001**.
Interactive API docs (Swagger UI) are at **http://localhost:8001/docs**.

### Local Python Package

Requires Python 3.12+ and Linux (or any OS for most collectors; systemd features require Linux).

```bash
git clone https://github.com/akash-sarkar-2001/pysyswatch.git
cd pysyswatch

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install the package
pip install .

# Verify
pysyswatch --version
pysyswatch status
```

### systemd Service

For running PySysWatch as a persistent native service without Docker:

```bash
# Install into a dedicated virtual environment
sudo python -m venv /opt/pysyswatch/venv
sudo /opt/pysyswatch/venv/bin/pip install .

# Create a dedicated user
sudo useradd -r -s /sbin/nologin pysyswatch

# Copy the environment file
sudo mkdir /etc/pysyswatch
sudo cp .env.example /etc/pysyswatch/.env
sudo nano /etc/pysyswatch/.env   # Set PYSYSWATCH_API_KEY

# Install and start the service
sudo cp systemd/pysyswatch.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pysyswatch

# Check status
sudo systemctl status pysyswatch
sudo journalctl -u pysyswatch -f
```

---

## Configuration

PySysWatch is configured via environment variables. Copy `.env.example` to `.env` to get started.

| Variable | Default | Description |
|---|---|---|
| `PYSYSWATCH_API_KEY` | *(empty)* | API key for REST API authentication. If empty, auth is disabled. |
| `PYSYSWATCH_DATABASE_URL` | `sqlite:///pysyswatch.db` | SQLAlchemy database URL (SQLite or PostgreSQL). |
| `PYSYSWATCH_LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

Generate a strong API key:

```bash
openssl rand -hex 32
```

---

## CLI Reference

All commands support a `--json` flag for machine-readable output, making them easy to pipe into other tools.

```
pysyswatch [OPTIONS] COMMAND [ARGS]...
```

### `status`

Quick system health snapshot — CPU, memory, and overall health state.

```bash
pysyswatch status
pysyswatch status --json
```

### `top`

Live-updating terminal dashboard (press `Ctrl+C` to exit).

```bash
pysyswatch top
pysyswatch top --refresh 5   # refresh every 5 seconds (default: 2)
```

### `diagnose`

Full diagnostic run. Evaluates all metrics against thresholds and prints a `HEALTHY`, `WARNING`, or `CRITICAL` verdict with a list of identified issues.

```bash
pysyswatch diagnose
pysyswatch diagnose --json
```

### `dashboard`

Start the FastAPI REST API and web dashboard.

```bash
pysyswatch dashboard
pysyswatch dashboard --port 9000 --host 0.0.0.0
```

### `cpu`

CPU usage and load averages.

```bash
pysyswatch cpu
pysyswatch cpu --json
```

### `memory`

RAM and swap usage.

```bash
pysyswatch memory
pysyswatch memory --json
```

### `disk`

Physical disk partition usage. Use `--threshold` to filter out low-utilization partitions.

```bash
pysyswatch disk
pysyswatch disk --threshold 80   # only show partitions above 80% usage
pysyswatch disk --json
```

### `network`

Network interface status and cumulative I/O counters.

```bash
pysyswatch network
pysyswatch network --json
```

### `processes`

Top running processes sorted by CPU or memory.

```bash
pysyswatch processes
pysyswatch processes --sort memory --limit 10
pysyswatch processes --json
```

### `ports`

Listening TCP/UDP ports and the processes bound to them.

```bash
pysyswatch ports
pysyswatch ports --json
```

### `services`

systemd service states. Use `--failed` to surface only failed units.

```bash
pysyswatch services
pysyswatch services --failed
pysyswatch services --json
```

### `logs`

Recent system log entries from the systemd journal.

```bash
pysyswatch logs
pysyswatch logs --lines 50 --level warning
pysyswatch logs --service nginx.service
pysyswatch logs --json
```

### `sensors`

Hardware temperature readings.

```bash
pysyswatch sensors
pysyswatch sensors --json
```

### `daemon`

Start the background monitoring daemon (typically managed by Docker or systemd).

```bash
pysyswatch daemon
```

---

## REST API

The API is served at `http://localhost:8001` when running via `pysyswatch dashboard` or Docker.

| Endpoint | Method | Description |
|---|---|---|
| `/healthz` | `GET` | Health check (used by Docker `HEALTHCHECK`) |
| `/docs` | `GET` | Interactive Swagger UI |
| `/redoc` | `GET` | ReDoc API documentation |
| `/dashboard` | `GET` | Browser-based live metrics dashboard |
| `/api/v1/metrics/cpu` | `GET` | CPU metrics |
| `/api/v1/metrics/memory` | `GET` | Memory metrics |
| `/api/v1/metrics/disk` | `GET` | Disk metrics |
| `/api/v1/metrics/network` | `GET` | Network metrics |
| `/api/v1/diagnostics/health` | `GET` | Full health evaluation |

### Authentication

When `PYSYSWATCH_API_KEY` is set, include it in requests:

```bash
curl -H "X-API-Key: <your-key>" http://localhost:8001/api/v1/metrics/cpu
```

---

## Development

### Setup

```bash
git clone https://github.com/akash-sarkar-2001/pysyswatch.git
cd pysyswatch
python -m venv venv && source venv/bin/activate
make setup       # installs the package + all dev dependencies
```

### Common Makefile Targets

| Target | Command | Description |
|---|---|---|
| `setup` | `make setup` | Install dev dependencies |
| `lint` | `make lint` | Run Ruff linter |
| `format` | `make format` | Auto-format with Ruff |
| `typecheck` | `make typecheck` | Run mypy (strict mode) |
| `check` | `make check` | Run lint + format + typecheck |
| `test` | `make test` | Run pytest with coverage |
| `docker-up` | `make docker-up` | Start Docker Compose stack |
| `docker-down` | `make docker-down` | Stop Docker Compose stack |
| `clean` | `make clean` | Remove build/cache artifacts |

### Code Standards

- **Type hints:** All code must be strictly type-hinted — enforced by `mypy --strict`.
- **Linting & formatting:** [Ruff](https://github.com/astral-sh/ruff) at line length 88. Run `make check` before committing.
- **Tests:** New collectors or features must have corresponding tests. Run `make test`.

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow.

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes and ensure quality checks pass:
   ```bash
   make check && make test
   ```
3. Submit a **pull request** describing the problem solved and the testing performed.

Please also review the [Code of Conduct](CODE_OF_CONDUCT.md) and [Security Policy](SECURITY.md).

---

## License

Distributed under the [MIT License](LICENSE).
