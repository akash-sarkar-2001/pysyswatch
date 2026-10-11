# Contributing to PySysWatch

Thank you for your interest in contributing! We aim to build a robust, maintainable systems engineering tool.

## Development Setup
1. Fork and clone the repository.
2. Create a virtual environment: `python -m venv venv && source venv/bin/activate`
3. Install development dependencies using the Makefile: `make setup`

## Code Standards
We treat PySysWatch as production infrastructure software. 
* **Type Hinting:** All code must be strictly type-hinted. We use `mypy --strict`.
* **Linting/Formatting:** We use `Ruff`. Run `make check` before committing.
* **Testing:** All new collectors or features must have corresponding tests. Run `make test`.

## Pull Request Process
1. Create a feature branch (`git checkout -b feature/your-feature`).
2. Ensure `make check` and `make test` pass locally.
3. Submit a PR describing the problem solved and testing performed.