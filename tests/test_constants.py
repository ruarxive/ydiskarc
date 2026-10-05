"""Tests for the named constants in ydiskarc.constants.

See openspec/changes/extract-magic-constants.
"""

import ydiskarc.constants as constants


def test_metadata_filename_constant():
    assert constants.METADATA_FILENAME == "_metadata.json"


def test_part_suffix_constant():
    assert constants.PART_SUFFIX == ".part"


def test_default_full_filename_constant():
    assert constants.DEFAULT_FULL_FILENAME == "dump.zip"


def test_http_status_constants_are_integers():
    for name in (
        "HTTP_OK",
        "HTTP_TOO_MANY_REQUESTS",
        "HTTP_INTERNAL_SERVER_ERROR",
        "HTTP_BAD_GATEWAY",
        "HTTP_SERVICE_UNAVAILABLE",
        "HTTP_GATEWAY_TIMEOUT",
    ):
        value = getattr(constants, name)
        assert isinstance(value, int), f"{name} should be int"
        assert 100 <= value < 600, f"{name} out of HTTP status range"


def test_http_too_many_requests_is_429():
    assert constants.HTTP_TOO_MANY_REQUESTS == 429


def test_json_key_constants_are_strings():
    for name in (
        "JSON_EMBEDDED",
        "JSON_ITEMS",
        "JSON_PATH",
        "JSON_TYPE",
        "JSON_SIZE",
        "JSON_FILE",
        "JSON_NAME",
        "JSON_PUBLIC_KEY",
        "JSON_HREF",
    ):
        value = getattr(constants, name)
        assert isinstance(value, str), f"{name} should be str"
        assert value, f"{name} must not be empty"


def test_json_type_constants():
    assert constants.JSON_TYPE_FILE == "file"
    assert constants.JSON_TYPE_DIR == "dir"


def test_default_api_list_limit():
    assert constants.DEFAULT_API_LIST_LIMIT == 1000


def test_header_constants():
    assert constants.HEADER_USER_AGENT == "User-Agent"
    assert constants.HEADER_RETRY_AFTER == "Retry-After"
    assert constants.HEADER_CONTENT_DISPOSITION == "Content-Disposition"
    assert constants.HEADER_RANGE == "Range"


def test_all_is_non_empty():
    assert constants.__all__
    # Every name in __all__ must actually be defined on the module.
    for name in constants.__all__:
        assert hasattr(constants, name), f"{name} listed in __all__ but missing"
