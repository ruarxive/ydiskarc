"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_metadata():
    """Sample Yandex.Disk metadata."""
    return {
        "name": "test_file.txt",
        "type": "file",
        "path": "disk:/test_file.txt",
        "size": 1024,
        "created": "2024-01-01T00:00:00Z",
        "modified": "2024-01-01T00:00:00Z",
        "mime_type": "text/plain"
    }


@pytest.fixture
def sample_dir_metadata():
    """Sample Yandex.Disk directory metadata."""
    return {
        "name": "test_dir",
        "type": "dir",
        "path": "disk:/test_dir",
        "created": "2024-01-01T00:00:00Z",
        "modified": "2024-01-01T00:00:00Z",
        "_embedded": {
            "items": [
                {
                    "name": "file1.txt",
                    "type": "file",
                    "path": "disk:/test_dir/file1.txt",
                    "size": 512,
                    "file": "https://example.com/file1.txt"
                }
            ]
        }
    }
