## Why

Magic strings and numbers are scattered across the codebase: `'_metadata.json'` appears in `core.py`, `processor.py`; `'dump.zip'` is hardcoded as the default filename in `processor.py`; status codes (`429`, `503`) and the Yandex API JSON keys (`'_embedded'`, `'items'`, `'path'`, `'type'`, `'size'`, `'file'`) appear inline in `processor.py` and `downloader.py`. This makes them easy to typo, hard to grep for, and impossible to override for tests.

## What Changes

- Create `ydiskarc/constants.py` with named constants:
  - File-system: `METADATA_FILENAME`, `_metadata_file` (alias), `DEFAULT_FULL_FILENAME`
  - HTTP: `HTTP_TOO_MANY_REQUESTS`, `HTTP_OK`, `HTTP_PARTIAL_CONTENT`
  - JSON keys: `JSON_EMBEDDED`, `JSON_ITEMS`, `JSON_PATH`, `JSON_TYPE`, `JSON_SIZE`, `JSON_FILE`, `JSON_DIR`, `JSON_PUBLIC_KEY`
  - Defaults: `DEFAULT_API_LIST_LIMIT = 1000`
- Replace every inline literal at call sites with the constant.
- Add a regression test asserting the constants exist and the call sites still produce the right filenames.

## Capabilities

### Modified Capabilities
- `core-architecture`: All repeating string/number literals must be named constants in a single module.

## Impact

- New file `ydiskarc/constants.py`.
- `ydiskarc/core.py`, `ydiskarc/cmds/processor.py`, `ydiskarc/downloader.py`, `ydiskarc/client.py` — replace literals.
- Tests assert constants exist and the integration test still passes.
- No runtime dependencies changed.