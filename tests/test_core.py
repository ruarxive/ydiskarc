"""Tests for core CLI module."""

import logging
from unittest.mock import MagicMock, patch

try:
    from typer.testing import CliRunner
except ImportError:
    # Fallback for older typer versions
    from click.testing import CliRunner

    # Typer apps can be tested with Click's CliRunner
    CliRunner = CliRunner

from ydiskarc.core import PACKAGE_LOGGER_NAME, app, setup_logging


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
        assert "Missing argument" in result.output or "missing" in result.output.lower()

    @patch("ydiskarc.core.Project")
    @patch("ydiskarc.client.YandexDiskClient.validate_yandex_url", return_value=True)
    def test_full_command_success(self, mock_validate, mock_project_class):
        """Test successful full command execution."""
        mock_project = MagicMock()
        mock_project_class.return_value = mock_project

        _ = self.runner.invoke(
            app, ["full", "https://disk.yandex.ru/d/test123", "--output", "/tmp/test"]
        )
        mock_project.full.assert_called_once()

    def test_sync_command_missing_url(self):
        """Test sync command fails without URL."""
        result = self.runner.invoke(app, ["sync"])
        assert result.exit_code != 0

    @patch("ydiskarc.core.Project")
    @patch("ydiskarc.client.YandexDiskClient.validate_yandex_url", return_value=True)
    def test_sync_command_success(self, mock_validate, mock_project_class):
        """Test successful sync command execution."""
        mock_project = MagicMock()
        mock_project_class.return_value = mock_project

        _ = self.runner.invoke(
            app, ["sync", "https://disk.yandex.ru/d/test123", "--output", "/tmp/test"]
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
        assert "1.2.0" in result.stdout

    def test_configure_command_is_registered(self):
        """The configure command MUST be reachable via the CLI."""
        result = self.runner.invoke(app, ["configure", "--help"])
        assert result.exit_code == 0
        assert "--key" in result.stdout

    @patch("ydiskarc.core.Project")
    def test_configure_command_calls_project_configure(self, mock_project_class):
        mock_project = MagicMock()
        mock_project_class.return_value = mock_project
        _ = self.runner.invoke(app, ["configure", "--key", "secret-token"])
        mock_project.configure.assert_called_once()
        kwargs = mock_project.configure.call_args.kwargs
        assert kwargs["key"] == "secret-token"

    def test_full_command_invalid_url(self):
        """Test full command rejects invalid URL."""
        result = self.runner.invoke(app, ["full", "https://example.com/invalid"])
        assert result.exit_code != 0
        assert "Invalid Yandex.Disk URL" in result.output or "Invalid Yandex.Disk URL" in str(
            result.exception
        )

    def test_sync_command_invalid_url(self):
        """Test sync command rejects invalid URL."""
        result = self.runner.invoke(app, ["sync", "not-a-url"])
        assert result.exit_code != 0
        assert "Invalid Yandex.Disk URL" in result.output or "Invalid Yandex.Disk URL" in str(
            result.exception
        )

    @patch("ydiskarc.core.Project")
    @patch("ydiskarc.client.YandexDiskClient.validate_yandex_url", return_value=True)
    def test_full_command_valid_url(self, mock_validate, mock_project_class):
        """Test full command accepts valid URL."""
        mock_project = MagicMock()
        mock_project_class.return_value = mock_project

        _ = self.runner.invoke(
            app, ["full", "https://disk.yandex.ru/d/ABC123", "--output", "/tmp/test"]
        )
        mock_project.full.assert_called_once()

    @patch("ydiskarc.core.Project")
    @patch("ydiskarc.client.YandexDiskClient.validate_yandex_url", return_value=True)
    def test_sync_command_valid_url(self, mock_validate, mock_project_class):
        """Test sync command accepts valid URL."""
        mock_project = MagicMock()
        mock_project_class.return_value = mock_project

        _ = self.runner.invoke(
            app, ["sync", "https://disk.yandex.ru/i/XYZ789", "--output", "/tmp/test"]
        )
        mock_project.sync.assert_called_once()


class TestSetupLogging:
    """Regression tests for setup_logging — see openspec/changes/fix-logging-configuration."""

    def setup_method(self):
        # Always start from a clean package logger so tests don't leak state.
        logger = logging.getLogger(PACKAGE_LOGGER_NAME)
        for h in list(logger.handlers):
            logger.removeHandler(h)
        logger.setLevel(logging.WARNING)

    def teardown_method(self):
        logger = logging.getLogger(PACKAGE_LOGGER_NAME)
        for h in list(logger.handlers):
            logger.removeHandler(h)
        logger.setLevel(logging.WARNING)

    def test_verbose_attaches_stream_handler_at_debug(self):
        setup_logging(verbose=True)
        logger = logging.getLogger(PACKAGE_LOGGER_NAME)
        assert logger.level == logging.DEBUG
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_quiet_keeps_no_ydiskarc_handlers(self):
        setup_logging(verbose=False)
        logger = logging.getLogger(PACKAGE_LOGGER_NAME)
        assert logger.level == logging.WARNING
        assert logger.handlers == []

    def test_verbose_emits_info_record(self, capsys):
        setup_logging(verbose=True)
        logger = logging.getLogger(PACKAGE_LOGGER_NAME)
        logger.info("hello-from-ydiskarc")
        captured = capsys.readouterr()
        assert "hello-from-ydiskarc" in captured.err

    def test_quiet_does_not_emit_info_record(self, capsys):
        setup_logging(verbose=False)
        logger = logging.getLogger(PACKAGE_LOGGER_NAME)
        logger.info("hello-from-ydiskarc")
        captured = capsys.readouterr()
        assert "hello-from-ydiskarc" not in captured.err

    def test_quiet_still_warns(self, caplog):
        """WARNING+ must still propagate when verbose=False so the embedder's
        root-logger handler (if any) sees real problems."""
        setup_logging(verbose=False)
        logger = logging.getLogger(PACKAGE_LOGGER_NAME)
        with caplog.at_level(logging.WARNING, logger=PACKAGE_LOGGER_NAME):
            logger.warning("warning-from-ydiskarc")
        assert any(
            rec.name == PACKAGE_LOGGER_NAME and "warning-from-ydiskarc" in rec.message
            for rec in caplog.records
        )

    def test_root_logger_not_touched_by_setup_logging(self):
        """setup_logging MUST NOT mutate process-global root-logger state."""
        root_before = logging.getLogger()
        root_handlers_before = list(root_before.handlers)
        root_level_before = root_before.level
        root_disabled_before = root_before.disabled

        setup_logging(verbose=True)
        setup_logging(verbose=False)

        root_after = logging.getLogger()
        assert root_after.handlers == root_handlers_before
        assert root_after.level == root_level_before
        assert root_after.disabled == root_disabled_before

    def test_other_libraries_not_muted(self):
        """A non-ydiskarc logger MUST still be free to emit at its own level
        after setup_logging(verbose=False)."""
        setup_logging(verbose=False)
        foreign = logging.getLogger("fake.third.party")
        assert foreign.disabled is False
        assert foreign.level == logging.NOTSET  # inheriting from root, not muted
