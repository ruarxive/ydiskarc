# Tests

This directory contains the test suite for ydiskarc.

## Running Tests

### Using pytest directly:
```bash
pytest
```

### Using pytest with verbose output:
```bash
pytest -v
```

### Running specific test file:
```bash
pytest tests/test_processor.py
```

### Running with coverage:
```bash
pytest --cov=ydiskarc --cov-report=html
```

### Using tox (runs tests in isolated environments):
```bash
tox
```

## Test Structure

- `test_processor.py` - Unit tests for processor module functions
- `test_core.py` - CLI tests using Typer test client
- `conftest.py` - Pytest fixtures and configuration

## Writing New Tests

When adding new functionality, please add corresponding tests:

1. Unit tests for individual functions
2. Integration tests for API interactions (use mocks)
3. CLI tests for command-line interface

## Mocking External Dependencies

Tests use `unittest.mock` to mock HTTP requests and file operations to avoid:
- Making actual network calls
- Creating/removing real files
- Depending on external services
