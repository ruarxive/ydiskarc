import logging
import os
import re
import subprocess
import urllib.parse
from email.message import EmailMessage as _EmailMessage  # noqa: F401
from typing import Any, Dict, Optional

import requests
from tqdm import tqdm

from . import constants
from .client import YandexDiskClient
from .config import config

__all__ = ["ResourceDownloader", "format_size", "parse_content_disposition", "sanitize_filename"]


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human-readable format."""
    size: float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


# RFC 5987 ``ext-value``: ``charset'language'value`` with optional percent-encoding.
_FILENAME_STAR_RE = re.compile(
    r"""filename\*\s*=\s*          # parameter name
        (?P<charset>[A-Za-z0-9\-]+)' # charset
        (?P<lang>[A-Za-z0-9\-]*)'    # optional language tag
        (?P<value>[^;]+)              # percent-encoded value
    """,
    re.VERBOSE,
)


def parse_content_disposition(header_value: Optional[str]) -> Optional[str]:
    """Parse a ``Content-Disposition`` header value and return the filename.

    Follows RFC 6266 / 5987: when both ``filename=`` and ``filename*=`` are
    present, ``filename*=`` takes precedence. The encoding declared in
    ``filename*`` is honored; default is UTF-8.

    Args:
        header_value: The raw ``Content-Disposition`` header value (without
            the field name), or ``None`` if the header is missing.

    Returns:
        The filename as declared by the server, or ``None`` if no filename
        parameter is present.
    """
    if not header_value:
        return None

    # First, look for ``filename*=`` (RFC 5987 extended encoding).
    m = _FILENAME_STAR_RE.search(header_value)
    if m:
        charset = m.group("charset") or "utf-8"
        encoded_value = m.group("value").strip().strip('"').strip("'")
        try:
            return urllib.parse.unquote(encoded_value, encoding=charset, errors="replace")
        except LookupError:
            return urllib.parse.unquote(encoded_value, errors="replace")

    # Otherwise fall back to ``filename=`` via email parser.
    msg = _EmailMessage()
    msg["Content-Disposition"] = header_value
    return msg.get_filename()


def sanitize_filename(name: str) -> str:
    """Sanitize a server-supplied filename for use as a local path component.

    Strips CR/LF/NUL and other control characters, replaces path separators
    with ``_``, removes surrounding whitespace and quotes. Returns an empty
    string if nothing usable remains (callers should fall back to a default).
    """
    if not name:
        return ""
    # Remove control chars (incl. CR/LF, NUL, tab).
    cleaned = "".join(ch for ch in name if 32 <= ord(ch) != 127 or ch == " ")
    # Drop surrounding quotes.
    cleaned = cleaned.strip().strip('"').strip("'")
    # Replace path separators with underscore.
    cleaned = cleaned.replace("/", "_").replace("\\", "_")
    # Drop anything still left that looks dangerous (NUL).
    cleaned = cleaned.replace("\x00", "")
    return cleaned.strip()


class ResourceDownloader:
    """Handles file downloads with tracking, resuming, and safety (.part files)."""

    def __init__(self, client: YandexDiskClient, verbose: bool = False):
        self.client = client
        self.verbose = verbose

    def _probe(
        self,
        url: str,
        params: Optional[Dict[str, Any]],
        headers: Dict[str, str],
        stream: bool,
    ) -> requests.Response:
        """Issue a probe request and reissue once on 429.

        Thin wrapper around :meth:`YandexDiskClient._request_with_backoff`
        that fixes ``stream`` and ``verify`` semantics. Centralises the rate
        limit retry pattern that previously appeared twice in :meth:`get_file`.
        """
        return self.client._request_with_backoff(
            "GET",
            url,
            params=params,
            headers=headers,
            stream=stream,
            verify=bool(config.verify) if config.verify is not None else True,
            timeout=config.timeout,
        )

    def get_file(
        self,
        url: str,
        filepath: Optional[str] = None,
        filename: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        aria2: bool = False,
        aria2path: Optional[str] = None,
        makedirs: bool = True,
        filesize: Optional[int] = None,
        resume: bool = True,
    ) -> None:
        """
        Download a file from a URL with progress tracking and resume support.
        Downloads are written to a `.part` extension during the process.
        """
        headers: Dict[str, str] = {}

        try:
            page = self._probe(url, params, headers, stream=True)
        except requests.exceptions.RequestException as e:
            if self.verbose:
                logging.error(f"Failed to download file from {url}: {e}")
            raise

        # Determine target filename
        if filename is None:
            cd = page.headers.get(constants.HEADER_CONTENT_DISPOSITION)
            parsed = parse_content_disposition(cd) if cd else None
            fname = sanitize_filename(parsed) if parsed else ""
            if not fname:
                fname = url.split("/")[-1]
            if filepath:
                filename = os.path.join(filepath, fname)
            else:
                filename = fname
        elif filepath is not None:
            filename = os.path.join(filepath, filename)

        # Temporary file for downloading
        part_filename = f"{filename}{constants.PART_SUFFIX}"

        # Check for existing file or partial file
        existing_size = 0
        if resume and os.path.exists(part_filename):
            existing_size = os.path.getsize(part_filename)
        elif resume and os.path.exists(filename):
            existing_size = os.path.getsize(filename)
            part_filename = filename  # Resume the actual file if no .part is present

        if existing_size > 0:
            page.close()
            headers[constants.HEADER_RANGE] = f"bytes={existing_size}-"
            if self.verbose:
                logging.info(f"Resuming download from byte {existing_size}")

            try:
                page = self._probe(url, params, headers, stream=True)
            except requests.exceptions.RequestException as e:
                if self.verbose:
                    logging.error(f"Failed to resume download from {url}: {e}")
                raise

        # Create directory if needed
        if makedirs and filepath:
            os.makedirs(filepath, exist_ok=True)

        if not aria2:
            remaining = (
                filesize - existing_size
                if existing_size > 0 and filesize is not None
                else (filesize if filesize is not None else None)
            )
            desc = f"Downloading {os.path.basename(filename)}" + (
                " (resuming)" if existing_size > 0 else ""
            )

            if self.verbose:
                logging.info(f"Retrieving file to {part_filename}")

            try:
                mode = "ab" if existing_size > 0 and resume else "wb"
                with open(part_filename, mode) as f:
                    total = existing_size
                    with tqdm(
                        total=remaining,
                        desc=desc,
                        unit="B",
                        unit_scale=True,
                        disable=filesize is None,
                    ) as pbar:
                        for chunk in page.iter_content(chunk_size=config.chunk_size):
                            if chunk:
                                f.write(chunk)
                                total += len(chunk)
                                if filesize is not None:
                                    pbar.update(len(chunk))

                # Rename .part to requested filename upon successful completion
                if part_filename != filename:
                    os.rename(part_filename, filename)

                if self.verbose:
                    logging.info(f"Successfully downloaded {filename} ({total} bytes)")
            except Exception as e:
                if self.verbose:
                    logging.error(f"Failed to write file {filename}: {e}")
                raise
        else:
            if aria2path is None:
                raise ValueError("aria2path must be provided when using aria2")

            dirpath = os.path.dirname(filename)
            basename = os.path.basename(filename)

            try:
                cmd = [aria2path, "--retry-wait=10", "--out", basename, url]
                if len(dirpath) > 0:
                    cmd = [aria2path, "--retry-wait=10", "-d", dirpath, "--out", basename, url]

                subprocess.run(cmd, check=True, timeout=3600)
                if self.verbose:
                    logging.info(f"Successfully downloaded {filename} using aria2")
            except subprocess.CalledProcessError as e:
                if self.verbose:
                    logging.error(f"aria2 download failed: {e}")
                raise
