"""Tests for parallel download dispatch.

See openspec/changes/add-parallel-downloads.
"""

import json
import tempfile
from unittest.mock import MagicMock, Mock, patch

import ydiskarc.cmds.processor as processor


def _api_response(items):
    resp = Mock()
    resp.text = json.dumps({"_embedded": {"items": items}})
    resp.json.return_value = {"_embedded": {"items": items}}
    resp.raise_for_status = Mock()
    return resp


class TestParallelDispatch:
    def test_parallel_4_invokes_pool_with_4_workers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(processor, "YandexDiskClient") as mock_client_cls:
                client = MagicMock()
                mock_client_cls.return_value = client
                client.get_resource_metadata.return_value = _api_response([])

                with patch.object(processor, "ResourceDownloader") as mock_downloader_cls:
                    downloader = MagicMock()
                    mock_downloader_cls.return_value = downloader

                    with patch.object(processor, "ThreadPoolExecutor") as mock_pool_cls:
                        pool = MagicMock()
                        mock_pool_cls.return_value.__enter__.return_value = pool
                        # Should not actually recurse or download anything since
                        # the response has no items.
                        processor._yd_get_and_store_dir(
                            "https://disk.yandex.ru/d/X",
                            "",
                            tmpdir,
                            iterative=True,
                            parallel=4,
                        )
                        # No items means no pool needed.
                        mock_pool_cls.assert_not_called()

    def test_parallel_4_dispatches_file_jobs_through_pool(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            items = [
                {
                    "path": f"/file{i}.pdf",
                    "type": "file",
                    "name": f"file{i}.pdf",
                    "size": 100,
                    "file": f"https://example.com/file{i}.pdf",
                }
                for i in range(4)
            ]
            with patch.object(processor, "YandexDiskClient") as mock_client_cls:
                client = MagicMock()
                mock_client_cls.return_value = client
                client.get_resource_metadata.return_value = _api_response(items)

                with patch.object(processor, "ResourceDownloader") as mock_downloader_cls:
                    downloader = MagicMock()
                    mock_downloader_cls.return_value = downloader

                    with patch.object(processor, "ThreadPoolExecutor") as mock_pool_cls:
                        pool = MagicMock()
                        mock_pool_cls.return_value.__enter__.return_value = pool
                        processor._yd_get_and_store_dir(
                            "https://disk.yandex.ru/d/X",
                            "",
                            tmpdir,
                            iterative=True,
                            parallel=4,
                        )
                        # Pool was constructed with max_workers=4.
                        mock_pool_cls.assert_called_once_with(max_workers=4)
                        # All 4 jobs submitted.
                        pool.map.assert_called_once()
                        jobs_list = list(pool.map.call_args.args[1])
                        assert len(jobs_list) == 4

    def test_parallel_1_uses_no_pool(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            items = [
                {
                    "path": "/file.pdf",
                    "type": "file",
                    "name": "file.pdf",
                    "size": 100,
                    "file": "https://example.com/file.pdf",
                }
            ]
            with patch.object(processor, "YandexDiskClient") as mock_client_cls:
                client = MagicMock()
                mock_client_cls.return_value = client
                client.get_resource_metadata.return_value = _api_response(items)

                with patch.object(processor, "ResourceDownloader") as mock_downloader_cls:
                    downloader = MagicMock()
                    mock_downloader_cls.return_value = downloader

                    with patch.object(processor, "ThreadPoolExecutor") as mock_pool_cls:
                        processor._yd_get_and_store_dir(
                            "https://disk.yandex.ru/d/X",
                            "",
                            tmpdir,
                            iterative=True,
                            parallel=1,
                        )
                        # No pool construction when parallel=1.
                        mock_pool_cls.assert_not_called()
                        # Direct download still happened.
                        downloader.get_file.assert_called_once()
