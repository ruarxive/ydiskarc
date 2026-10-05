## Why

The `full` command for a single-file public resource (`https://disk.yandex.ru/i/...`) currently does **two** API calls: `get_resource_metadata` (to read `type`/`size`) followed by `get_download_link` (to fetch the actual download URL). The first call returns a `file` field that is the direct download URL — the second call is redundant.

For directory resources (`https://disk.yandex.ru/d/...`), the directory walker already uses the `file` field from the listing, so `get_download_link` is necessary only as a fallback.

## What Changes

- In `_yd_get_full`:
  - When the metadata response is a `file` resource AND a `file` URL is present, use it directly and skip the second `get_download_link` call.
  - When the metadata response is a `dir` resource, fall back to `get_download_link` (which produces the ZIP archive URL).
- Add a regression test that mocks both API endpoints and asserts the second endpoint is **not** called when the first one returns a `file` URL.

## Impact

- `ydiskarc/cmds/processor.py` — `_yd_get_full` short-circuits when metadata already has `file`.
- `tests/test_processor.py` — new test class `TestFullSkipDuplicateApiCall`.
- No new dependencies.
- No public-API changes (one less HTTP call on the hot path).