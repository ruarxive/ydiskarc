"""Tests for the centralised rate-limit retry in YandexDiskClient.

See openspec/changes/dedupe-rate-limit-retry.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from ydiskarc.client import YandexDiskClient


def _make_response(status_code: int, json_payload=None, headers=None):
    resp = Mock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.raise_for_status = Mock()
    if json_payload is not None:
        resp.json.return_value = json_payload
    else:
        resp.json = Mock()
    return resp


class TestRequestWithBackoff:
    def test_first_attempt_200_no_retry(self):
        client = YandexDiskClient()
        session = MagicMock()
        ok = _make_response(200, json_payload={"href": "https://example.com/dl"})
        session.request.return_value = ok
        client.session = session

        resp = client._request_with_backoff("GET", "https://api/x")

        assert resp is ok
        assert session.request.call_count == 1
        ok.raise_for_status.assert_called_once()

    def test_429_then_200_retries_once(self):
        client = YandexDiskClient()
        session = MagicMock()
        rate_limited = _make_response(429, headers={"Retry-After": "0"})
        ok = _make_response(200, json_payload={"href": "https://example.com/dl"})
        session.request.side_effect = [rate_limited, ok]
        client.session = session

        with patch.object(client, "handle_rate_limit") as handle:
            resp = client._request_with_backoff("GET", "https://api/x")

        assert resp is ok
        assert session.request.call_count == 2
        handle.assert_called_once_with(rate_limited)
        ok.raise_for_status.assert_called_once()

    def test_429_twice_raises_on_status(self):
        client = YandexDiskClient()
        session = MagicMock()
        rl1 = _make_response(429, headers={"Retry-After": "0"})
        rl2 = _make_response(429, headers={"Retry-After": "0"})
        rl2.raise_for_status.side_effect = RuntimeError("still rate limited")
        session.request.side_effect = [rl1, rl2]
        client.session = session

        with patch.object(client, "handle_rate_limit") as handle:
            with pytest.raises(RuntimeError, match="still rate limited"):
                client._request_with_backoff("GET", "https://api/x")

        assert handle.call_count == 1  # only the first 429 triggers backoff
        assert session.request.call_count == 2


class TestGetResourceMetadataUsesBackoff:
    def test_delegates_to_request_with_backoff(self):
        from ydiskarc.config import config

        client = YandexDiskClient()
        ok = _make_response(200, json_payload={"type": "dir", "_embedded": {}})
        with patch.object(client, "_request_with_backoff", return_value=ok) as helper:
            client.get_resource_metadata("https://disk.yandex.ru/d/X")
        helper.assert_called_once()
        args, kwargs = helper.call_args
        assert args[0] == "GET"
        assert args[1] == client.api_url
        assert kwargs["params"]["public_key"] == "https://disk.yandex.ru/d/X"
        assert kwargs["timeout"] == config.timeout


class TestGetDownloadLinkUsesBackoff:
    def test_delegates_to_request_with_backoff(self):
        client = YandexDiskClient()
        ok = _make_response(200, json_payload={"href": "https://example.com/dl"})
        with patch.object(client, "_request_with_backoff", return_value=ok) as helper:
            link = client.get_download_link("https://disk.yandex.ru/d/X")
        assert link == "https://example.com/dl"
        helper.assert_called_once()
        args, kwargs = helper.call_args
        assert args[0] == "GET"
        assert kwargs["params"] == {"public_key": "https://disk.yandex.ru/d/X"}

    def test_missing_href_raises_value_error(self):
        client = YandexDiskClient()
        ok = _make_response(200, json_payload={"unexpected": "shape"})
        with patch.object(client, "_request_with_backoff", return_value=ok):
            with pytest.raises(ValueError, match="No download URL"):
                client.get_download_link("https://disk.yandex.ru/d/X")
