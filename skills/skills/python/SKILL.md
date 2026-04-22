---
name: python
description: Python Best Practices
---

# Python Best Practices
# For GitHub Copilot

## Code Style

- Follow PEP 8; use `ruff` for linting and formatting
- Use f-strings for string formatting (not `.format()` or `%`)
- Prefer `pathlib.Path` over `os.path`
- Use `dataclasses` or `pydantic` for data models

## Type Hints

- Always use type hints for function signatures
- Use `from __future__ import annotations` for forward references
- Prefer `X | Y` union syntax (Python 3.10+) over `Optional[X]`

## Error Handling

- Use specific exception types, not bare `except:`
- Log exceptions with context: `logger.exception("msg", extra={...})`
- Use custom exception classes for domain errors

## Dependencies

- Pin dependencies in `pyproject.toml` with minimum versions
- Use virtual environments (`venv` or `uv`)
- Prefer `httpx` over `requests` for async-compatible HTTP

## Testing

- Use `pytest` with `pytest-asyncio` for async tests
- Use `unittest.mock` or `pytest-mock` for mocking
- Structure tests: `tests/unit/`, `tests/integration/`
- Use fixtures for shared setup
