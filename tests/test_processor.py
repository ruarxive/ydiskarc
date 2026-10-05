"""Unit tests for the new architecture."""

import json
import os
import stat
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from ydiskarc.client import YandexDiskClient
from ydiskarc.cmds import processor as processor_module
from ydiskarc.cmds.processor import (
    PathTraversalError,
    Project,
    safe_join,
)
from ydiskarc.downloader import ResourceDownloader

# Public API for the recursive walker is the Project class. The module-level
# functions are private; tests that exercise them directly use the underscored
# names so the facade rule is documented in tests.
_scan_directory_for_stats = processor_module._scan_directory_for_stats
_yd_get_and_store_dir = processor_module._yd_get_and_store_dir
_yd_get_full = processor_module._yd_get_full


class TestClient:
    def test_validate_yandex_url_valid_directory(self):
        assert YandexDiskClient.validate_yandex_url("https://disk.yandex.ru/d/ABC123") is True

    def test_validate_yandex_url_invalid(self):
        assert YandexDiskClient.validate_yandex_url("https://example.com/file") is False


class TestDownloader:
    @patch("ydiskarc.client.YandexDiskClient._create_session_with_retries")
    @patch("ydiskarc.downloader.open", create=True)
    @patch("ydiskarc.downloader.os.path.exists")
    @patch("ydiskarc.downloader.os.rename")
    def test_get_file_basic(self, mock_rename, mock_exists, mock_open, mock_session_factory):
        mock_exists.return_value = False
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.iter_content.return_value = [b"file content"]
        mock_response.raise_for_status = Mock()
        # Code now uses session.request (via _request_with_backoff) instead of
        # session.get — keep both aliases so the assertion works either way.
        mock_session.get.return_value = mock_response
        mock_session.request.return_value = mock_response
        mock_session_factory.return_value = mock_session

        client = YandexDiskClient()
        # Override session to use our mock
        client.session = mock_session

        downloader = ResourceDownloader(client)

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            downloader.get_file("http://example.com/file.txt", filepath=tmpdir)

        # Either the legacy .get path or the new .request path should have
        # been hit at least once.
        assert mock_session.request.called or mock_session.get.called
        mock_file.write.assert_called()


class TestYdGetFull:
    @patch("ydiskarc.cmds.processor.YandexDiskClient")
    @patch("ydiskarc.cmds.processor.ResourceDownloader")
    def test_yd_get_full_basic(self, mock_downloader_cls, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_meta_resp = Mock()
        mock_meta_resp.json.return_value = {"type": "file"}
        mock_meta_resp.raise_for_status = Mock()
        mock_client.get_resource_metadata.return_value = mock_meta_resp

        mock_client.get_download_link.return_value = "http://example.com/download"

        mock_downloader = MagicMock()
        mock_downloader_cls.return_value = mock_downloader

        with tempfile.TemporaryDirectory() as tmpdir:
            _yd_get_full("https://disk.yandex.ru/d/test123", tmpdir, None, False)

        mock_client.get_resource_metadata.assert_called_once()
        mock_client.get_download_link.assert_called_once()
        mock_downloader.get_file.assert_called_once()


class TestFullSkipDuplicateApiCall:
    """See openspec/changes/skip-duplicate-full-api-call."""

    @patch("ydiskarc.cmds.processor.YandexDiskClient")
    @patch("ydiskarc.cmds.processor.ResourceDownloader")
    def test_file_resource_with_file_url_skips_get_download_link(
        self, mock_downloader_cls, mock_client_cls
    ):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_meta_resp = Mock()
        mock_meta_resp.json.return_value = {
            "type": "file",
            "size": 12345,
            "file": "https://downloader.disk.yandex.ru/direct/...",
        }
        mock_meta_resp.raise_for_status = Mock()
        mock_client.get_resource_metadata.return_value = mock_meta_resp
        mock_client.get_download_link.return_value = "should-not-be-used"

        mock_downloader = MagicMock()
        mock_downloader_cls.return_value = mock_downloader

        with tempfile.TemporaryDirectory() as tmpdir:
            _yd_get_full("https://disk.yandex.ru/i/X", tmpdir, None, False)

        # Second API call MUST be skipped.
        mock_client.get_download_link.assert_not_called()
        mock_client.get_resource_metadata.assert_called_once()
        # Downloader received the direct URL from metadata.
        download_args = mock_downloader.get_file.call_args.args
        assert download_args[0] == "https://downloader.disk.yandex.ru/direct/..."

    @patch("ydiskarc.cmds.processor.YandexDiskClient")
    @patch("ydiskarc.cmds.processor.ResourceDownloader")
    def test_file_resource_without_file_url_falls_back(self, mock_downloader_cls, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_meta_resp = Mock()
        mock_meta_resp.json.return_value = {"type": "file", "size": 12345}
        mock_meta_resp.raise_for_status = Mock()
        mock_client.get_resource_metadata.return_value = mock_meta_resp
        mock_client.get_download_link.return_value = "https://downloader.disk.yandex.ru/fallback"

        mock_downloader = MagicMock()
        mock_downloader_cls.return_value = mock_downloader

        with tempfile.TemporaryDirectory() as tmpdir:
            _yd_get_full("https://disk.yandex.ru/i/X", tmpdir, None, False)

        mock_client.get_download_link.assert_called_once()

    @patch("ydiskarc.cmds.processor.YandexDiskClient")
    @patch("ydiskarc.cmds.processor.ResourceDownloader")
    @patch("ydiskarc.cmds.processor._scan_directory_for_stats")
    def test_dir_resource_always_uses_get_download_link(
        self, mock_scan, mock_downloader_cls, mock_client_cls
    ):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_meta_resp = Mock()
        mock_meta_resp.json.return_value = {
            "type": "dir",
            "_embedded": {"items": []},
            "file": "https://should-be-ignored-because-type-is-dir",
        }
        mock_meta_resp.raise_for_status = Mock()
        mock_client.get_resource_metadata.return_value = mock_meta_resp
        mock_client.get_download_link.return_value = "https://downloader.disk.yandex.ru/archive.zip"

        mock_downloader = MagicMock()
        mock_downloader_cls.return_value = mock_downloader
        mock_scan.return_value = (0, 0)

        with tempfile.TemporaryDirectory() as tmpdir:
            _yd_get_full("https://disk.yandex.ru/d/X", tmpdir, None, False)

        mock_client.get_download_link.assert_called_once()
        download_args = mock_downloader.get_file.call_args.args
        assert download_args[0] == "https://downloader.disk.yandex.ru/archive.zip"


class TestYdGetAndStoreDir:
    @patch("ydiskarc.cmds.processor.YandexDiskClient")
    @patch("ydiskarc.cmds.processor.ResourceDownloader")
    def test_yd_get_and_store_dir_basic(self, mock_downloader_cls, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_resp = Mock()
        mock_resp.text = json.dumps({"name": "test_dir", "type": "dir", "_embedded": {"items": []}})
        mock_resp.json.return_value = {
            "name": "test_dir",
            "type": "dir",
            "_embedded": {"items": []},
        }
        mock_resp.raise_for_status = Mock()
        mock_client.get_resource_metadata.return_value = mock_resp

        with tempfile.TemporaryDirectory() as tmpdir:
            result = _yd_get_and_store_dir(
                "https://disk.yandex.ru/d/test123",
                "",
                tmpdir,
                update=False,
                nofiles=True,
                iterative=False,
            )
            assert result is not None
            assert os.path.exists(os.path.join(tmpdir, "_metadata.json"))


class TestProject:
    @patch("builtins.print")
    @patch("ydiskarc.cmds.processor._scan_directory_for_stats")
    @patch("ydiskarc.cmds.processor._yd_get_and_store_dir")
    def test_project_sync(self, mock_yd_get, mock_scan, mock_print):
        mock_scan.return_value = (1, 100)
        project = Project()
        with tempfile.TemporaryDirectory() as tmpdir:
            project.sync("https://disk.yandex.ru/d/test123", tmpdir, False, False)
        mock_yd_get.assert_called_once()

    @patch("ydiskarc.cmds.processor._yd_get_full")
    def test_project_full(self, mock_yd_get):
        project = Project()
        with tempfile.TemporaryDirectory() as tmpdir:
            project.full("https://disk.yandex.ru/d/test123", tmpdir, None, False)
        mock_yd_get.assert_called_once()


class TestPublicSurface:
    """The recursive walker functions are private to the processor module;
    only Project, PathTraversalError, and safe_join are public."""

    def test_cannot_import_unprefixed_yd_get_and_store_dir(self):
        with pytest.raises(ImportError):
            from ydiskarc.cmds.processor import yd_get_and_store_dir  # noqa: F401

    def test_cannot_import_unprefixed_scan_directory_for_stats(self):
        with pytest.raises(ImportError):
            from ydiskarc.cmds.processor import scan_directory_for_stats  # noqa: F401

    def test_cannot_import_unprefixed_yd_get_full(self):
        with pytest.raises(ImportError):
            from ydiskarc.cmds.processor import yd_get_full  # noqa: F401

    def test_can_import_public_names(self):
        # These imports succeed.
        from ydiskarc.cmds.processor import PathTraversalError, Project, safe_join  # noqa: F401


class TestSafeJoin:
    """Regression tests for safe_join — see openspec/changes/fix-path-traversal."""

    def test_allows_normal_nested_path(self, tmp_path):
        result = safe_join(str(tmp_path), "SubDir", "file.pdf")
        assert result == os.path.realpath(os.path.join(str(tmp_path), "SubDir", "file.pdf"))
        assert os.path.commonpath([str(tmp_path), result]) == str(tmp_path)

    def test_allows_path_with_leading_slash_segments(self, tmp_path):
        # Yandex returns paths like "/SubDir/file.pdf" — leading slash on a
        # segment is OK as long as it doesn't escape the base.
        result = safe_join(str(tmp_path), "/SubDir", "file.pdf")
        assert str(tmp_path) in result or result.startswith(str(tmp_path))

    def test_rejects_dotdot_segment(self, tmp_path):
        with pytest.raises(PathTraversalError):
            safe_join(str(tmp_path), "..", "etc", "passwd")

    def test_rejects_dotdot_inside_segment(self, tmp_path):
        with pytest.raises(PathTraversalError):
            safe_join(str(tmp_path), "foo/../../etc/passwd")

    def test_rejects_drive_letter(self, tmp_path):
        # Windows-style drive letter should be rejected on any platform.
        with pytest.raises(PathTraversalError):
            safe_join(str(tmp_path), "C:", "Windows", "System32")

    def test_absolute_path_treated_as_relative_to_base(self, tmp_path):
        # "/etc/passwd" is just "etc/passwd" relative to base — not an attack.
        # The Yandex API returns paths starting with "/" and we honor that.
        result = safe_join(str(tmp_path), "/etc", "passwd")
        assert result.startswith(str(tmp_path))

    def test_rejects_empty_base(self):
        with pytest.raises(PathTraversalError):
            safe_join("", "foo")

    def test_strips_whitespace_and_skips_empty(self, tmp_path):
        result = safe_join(str(tmp_path), "  SubDir  ", "", "  file.pdf  ")
        assert result.endswith(os.path.join("SubDir", "file.pdf"))

    def test_handles_backslash_separators(self, tmp_path):
        # On POSIX backslash is a normal char, but we treat it as a separator
        # to defend against Windows path smuggle.
        result = safe_join(str(tmp_path), "SubDir\\file.pdf")
        assert result.endswith(os.path.join("SubDir", "file.pdf"))


class TestScanDirectoryTraversal:
    """End-to-end: scan_directory_for_stats MUST skip hostile API paths."""

    @patch("ydiskarc.client.YandexDiskClient._create_session_with_retries")
    def test_traversal_path_is_skipped(self, mock_session_factory):
        mock_session = MagicMock()
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "_embedded": {
                "items": [
                    {"path": "/legit/file.pdf", "type": "file", "size": 100},
                    {"path": "../../../etc/passwd", "type": "file", "size": 999},
                ]
            }
        }
        mock_resp.raise_for_status = Mock()
        mock_session.get.return_value = mock_resp
        mock_session.request.return_value = mock_resp
        mock_session_factory.return_value = mock_session

        client = YandexDiskClient()
        client.session = mock_session

        with patch("ydiskarc.cmds.processor.YandexDiskClient", return_value=client):
            with tempfile.TemporaryDirectory() as tmpdir:
                count, total = _scan_directory_for_stats(
                    "https://disk.yandex.ru/d/test123",
                    "",
                    tmpdir,
                    update=False,
                    nofiles=False,
                    verbose=False,
                )
                # Only the legitimate file counts; the traversal attempt is skipped.
                assert count == 1
                assert total == 100


class TestProjectConfigure:
    """See openspec/changes/resolve-configure-cmd."""

    def test_writes_file_with_restricted_perms(self, tmp_path):
        import yaml as _yaml

        Project().configure(key="my-oauth-token", projectdir=str(tmp_path))

        cfg_file = tmp_path / ".ydiskarc"
        assert cfg_file.exists()
        data = _yaml.safe_load(cfg_file.read_text(encoding="utf8"))
        assert data["keys"]["yandex_oauth"] == "my-oauth-token"

        # On POSIX the file MUST be 0o600 (or stricter); on Windows we skip.
        if hasattr(os, "chmod") and os.name == "posix":
            mode = stat.S_IMODE(cfg_file.stat().st_mode)
            assert mode == 0o600, f"expected 0o600, got {oct(mode)}"

    def test_preserves_existing_config(self, tmp_path):
        import yaml as _yaml

        cfg_file = tmp_path / ".ydiskarc"
        cfg_file.write_text(
            "keys:\n  yandex_oauth: old-key\ncustom_field: keep-me\n",
            encoding="utf8",
        )

        Project().configure(key="new-key", projectdir=str(tmp_path))

        data = _yaml.safe_load(cfg_file.read_text(encoding="utf8"))
        assert data["keys"]["yandex_oauth"] == "new-key"
        assert data["custom_field"] == "keep-me"
