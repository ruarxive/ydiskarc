"""Tests for core CLI module."""

from unittest.mock import patch, MagicMock

import pytest
try:
    from typer.testing import CliRunner
except ImportError:
    # Fallback for older typer versions
    from click.testing import CliRunner
    import typer
    # Typer apps can be tested with Click's CliRunner
    CliRunner = CliRunner

from ydiskarc.core import app


class TestCLI:
    """Tests for CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_app_exists(self):
        """Test that the Typer app is properly configured."""
        assert app is not None
        assert app.info.name == "ydiskarc"

    def test_full_command_help(self):
        """Test full command help text."""
        result = self.runner.invoke(app, ["full", "--help"])
        assert result.exit_code == 0
        assert "Download a full copy" in result.stdout

    def test_sync_command_help(self):
        """Test sync command help text."""
        result = self.runner.invoke(app, ["sync", "--help"])
        assert result.exit_code == 0
        assert "Synchronize files" in result.stdout

    def test_full_command_missing_url(self):
        """Test full command fails without URL."""
        result = self.runner.invoke(app, ["full"])
        assert result.exit_code != 0
        assert "Public resource URL required" in result.stdout or "Public resource URL required" in str(result.exception)

    @patch('ydiskarc.core.Project')
    def test_full_command_success(self, mock_project_class):
        """Test successful full command execution."""
        mock_project = MagicMock()
        mock_project_class.return_value = mock_project

        result = self.runner.invoke(
            app,
            ["full", "--url", "https://disk.yandex.ru/d/test123", "--output", "/tmp/test"]
        )
        # May exit with error if Project raises, but command should be invoked
        mock_project.full.assert_called_once()

    def test_sync_command_missing_url(self):
        """Test sync command fails without URL."""
        result = self.runner.invoke(app, ["sync"])
        assert result.exit_code != 0

    @patch('ydiskarc.core.Project')
    def test_sync_command_success(self, mock_project_class):
        """Test successful sync command execution."""
        mock_project = MagicMock()
        mock_project_class.return_value = mock_project

        result = self.runner.invoke(
            app,
            ["sync", "--url", "https://disk.yandex.ru/d/test123", "--output", "/tmp/test"]
        )
        mock_project.sync.assert_called_once()

    def test_verbose_flag(self):
        """Test verbose flag is accepted."""
        result = self.runner.invoke(app, ["full", "--help"])
        assert result.exit_code == 0
        assert "--verbose" in result.stdout or "-v" in result.stdout

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "ydiskarc" in result.stdout
        assert "1.0.1" in result.stdout

    def test_full_command_invalid_url(self):
        """Test full command rejects invalid URL."""
        result = self.runner.invoke(
            app,
            ["full", "--url", "https://example.com/invalid"]
        )
        assert result.exit_code != 0
        assert "Invalid Yandex.Disk URL" in result.stdout

    def test_sync_command_invalid_url(self):
        """Test sync command rejects invalid URL."""
        result = self.runner.invoke(
            app,
            ["sync", "--url", "not-a-url"]
        )
        assert result.exit_code != 0
        assert "Invalid Yandex.Disk URL" in result.stdout

    @patch('ydiskarc.core.Project')
    def test_full_command_valid_url(self, mock_project_class):
        """Test full command accepts valid URL."""
        mock_project = MagicMock()
        mock_project_class.return_value = mock_project

        result = self.runner.invoke(
            app,
            ["full", "--url", "https://disk.yandex.ru/d/ABC123", "--output", "/tmp/test"]
        )
        # Should pass URL validation and call Project.full
        mock_project.full.assert_called_once()

    @patch('ydiskarc.core.Project')
    def test_sync_command_valid_url(self, mock_project_class):
        """Test sync command accepts valid URL."""
        mock_project = MagicMock()
        mock_project_class.return_value = mock_project

        result = self.runner.invoke(
            app,
            ["sync", "--url", "https://disk.yandex.ru/i/XYZ789", "--output", "/tmp/test"]
        )
        # Should pass URL validation and call Project.sync
        mock_project.sync.assert_called_once()
