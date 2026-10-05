"""Project-wide constants for ydiskarc.

Single source of truth for repeated string and number literals (filenames,
HTTP status codes, Yandex.Disk API JSON keys, pagination defaults). See
``openspec/changes/extract-magic-constants``.
"""

from typing import Final

# ---------------------------------------------------------------------------
# File-system conventions
# ---------------------------------------------------------------------------

METADATA_FILENAME: Final[str] = "_metadata.json"
"""Sidecar JSON written next to a directory or downloaded file."""

PART_SUFFIX: Final[str] = ".part"
"""Suffix used while a download is in progress."""

DEFAULT_FULL_FILENAME: Final[str] = "dump.zip"
"""Default output filename for the ``full`` command when downloading a
directory as a ZIP archive."""


# ---------------------------------------------------------------------------
# HTTP status codes
# ---------------------------------------------------------------------------

HTTP_OK: Final[int] = 200
HTTP_PARTIAL_CONTENT: Final[int] = 206
HTTP_TOO_MANY_REQUESTS: Final[int] = 429
HTTP_INTERNAL_SERVER_ERROR: Final[int] = 500
HTTP_BAD_GATEWAY: Final[int] = 502
HTTP_SERVICE_UNAVAILABLE: Final[int] = 503
HTTP_GATEWAY_TIMEOUT: Final[int] = 504


# ---------------------------------------------------------------------------
# Yandex.Disk Public API — JSON keys
# ---------------------------------------------------------------------------

JSON_EMBEDDED: Final[str] = "_embedded"
JSON_ITEMS: Final[str] = "items"
JSON_PATH: Final[str] = "path"
JSON_TYPE: Final[str] = "type"
JSON_SIZE: Final[str] = "size"
JSON_FILE: Final[str] = "file"
JSON_NAME: Final[str] = "name"
JSON_CREATED: Final[str] = "created"
JSON_MODIFIED: Final[str] = "modified"
JSON_MD5: Final[str] = "md5"
JSON_SHA256: Final[str] = "sha256"
JSON_MIME_TYPE: Final[str] = "mime_type"
JSON_PUBLIC_KEY: Final[str] = "public_key"
JSON_PUBLIC_URL: Final[str] = "public_url"
JSON_HREF: Final[str] = "href"

JSON_TYPE_FILE: Final[str] = "file"
JSON_TYPE_DIR: Final[str] = "dir"


# ---------------------------------------------------------------------------
# Default API pagination
# ---------------------------------------------------------------------------

DEFAULT_API_LIST_LIMIT: Final[int] = 1000
"""Default ``limit`` passed to the public resources API when listing items."""


# ---------------------------------------------------------------------------
# HTTP headers
# ---------------------------------------------------------------------------

HEADER_USER_AGENT: Final[str] = "User-Agent"
HEADER_RETRY_AFTER: Final[str] = "Retry-After"
HEADER_CONTENT_DISPOSITION: Final[str] = "Content-Disposition"
HEADER_RANGE: Final[str] = "Range"


__all__ = [
    "METADATA_FILENAME",
    "PART_SUFFIX",
    "DEFAULT_FULL_FILENAME",
    "HTTP_OK",
    "HTTP_PARTIAL_CONTENT",
    "HTTP_TOO_MANY_REQUESTS",
    "HTTP_INTERNAL_SERVER_ERROR",
    "HTTP_BAD_GATEWAY",
    "HTTP_SERVICE_UNAVAILABLE",
    "HTTP_GATEWAY_TIMEOUT",
    "JSON_EMBEDDED",
    "JSON_ITEMS",
    "JSON_PATH",
    "JSON_TYPE",
    "JSON_SIZE",
    "JSON_FILE",
    "JSON_NAME",
    "JSON_CREATED",
    "JSON_MODIFIED",
    "JSON_MD5",
    "JSON_SHA256",
    "JSON_MIME_TYPE",
    "JSON_PUBLIC_KEY",
    "JSON_PUBLIC_URL",
    "JSON_HREF",
    "JSON_TYPE_FILE",
    "JSON_TYPE_DIR",
    "DEFAULT_API_LIST_LIMIT",
    "HEADER_USER_AGENT",
    "HEADER_RETRY_AFTER",
    "HEADER_CONTENT_DISPOSITION",
    "HEADER_RANGE",
]
