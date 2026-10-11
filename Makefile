.PHONY: setup lint format check test docker-up docker-down clean

setup:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .

check: lint format typecheck

typecheck:
	mypy src

test:
	pytest tests/ --cov=pysyswatch

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +