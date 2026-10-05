import logging
import re
import time
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import constants
from .config import config

__all__ = ["YandexDiskClient"]


class YandexDiskClient:
    """Client for interacting with Yandex.Disk API."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.api_url = config.api_resources_url
        self.api_download_url = config.api_download_url
        self.session = self._create_session_with_retries()

    def _create_session_with_retries(self) -> requests.Session:
        """Create a requests session with retry logic and rate limiting handling."""
        session = requests.Session()
        retry_strategy = Retry(
            total=config.max_retries,
            backoff_factor=config.retry_backoff_factor,
            status_forcelist=[
                constants.HTTP_TOO_MANY_REQUESTS,
                constants.HTTP_INTERNAL_SERVER_ERROR,
                constants.HTTP_BAD_GATEWAY,
                constants.HTTP_SERVICE_UNAVAILABLE,
                constants.HTTP_GATEWAY_TIMEOUT,
            ],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=config.pool_maxsize,
            pool_maxsize=config.pool_maxsize,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        headers = {constants.HEADER_USER_AGENT: config.user_agent or ""}
        session.headers.update(headers)
        return session

    def handle_rate_limit(self, resp: requests.Response) -> None:
        """Handle rate limiting by waiting for the specified time."""
        if resp.status_code == constants.HTTP_TOO_MANY_REQUESTS:
            retry_after = int(resp.headers.get(constants.HEADER_RETRY_AFTER, 60))
            if self.verbose:
                logging.warning(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)

    def _request_with_backoff(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Issue an HTTP request and reissue once on 429.

        Centralises the ``if status == 429: wait; retry`` pattern that
        previously appeared in three call sites. Calls
        :meth:`requests.Response.raise_for_status` before returning so callers
        don't have to.

        Args:
            method: HTTP method (``"GET"`` / ``"POST"``).
            url: Target URL.
            **kwargs: Forwarded to ``Session.request`` (``params``,
                ``timeout``, ``headers``, ...).

        Returns:
            The final response, after at most one reissue on 429.
        """
        resp = self.session.request(method, url, **kwargs)
        if resp.status_code == constants.HTTP_TOO_MANY_REQUESTS:
            self.handle_rate_limit(resp)
            resp = self.session.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp

    @staticmethod
    def validate_yandex_url(url: str) -> bool:
        """Validate Yandex.Disk public resource URL."""
        patterns = [
            r"https://disk\.yandex\.ru/d/[A-Za-z0-9_-]+",
            r"https://disk\.yandex\.ru/i/[A-Za-z0-9_-]+",
            r"https://disk\.yandex\.com/d/[A-Za-z0-9_-]+",
            r"https://disk\.yandex\.com/i/[A-Za-z0-9_-]+",
        ]
        return any(re.match(pattern, url) for pattern in patterns)

    def get_resource_metadata(
        self, url: str, path: Optional[str] = None, limit: int = constants.DEFAULT_API_LIST_LIMIT
    ) -> requests.Response:
        """Fetch resource metadata from Yandex.Disk API."""
        params: Dict[str, Any] = {constants.JSON_PUBLIC_KEY: url}
        if path is not None:
            params[constants.JSON_PATH] = path
            params["limit"] = limit

        return self._request_with_backoff(
            "GET", self.api_url, params=params, timeout=config.timeout
        )

    def get_download_link(self, url: str) -> str:
        """Get the direct download link for a public resource."""
        resp = self._request_with_backoff(
            "GET",
            self.api_download_url,
            params={constants.JSON_PUBLIC_KEY: url},
            timeout=config.timeout,
        )
        data = resp.json()
        if constants.JSON_HREF not in data:
            raise ValueError(f"No download URL found for {url}")

        return data[constants.JSON_HREF]
