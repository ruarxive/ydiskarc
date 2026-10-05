## 1. Implementation

- [ ] 1.1 In `_yd_get_full`, after fetching metadata, check `metadata_data.get("type") == "file"` and `metadata_data.get("file")` — if both, pass that URL directly to `downloader.get_file` and skip `get_download_link`.
- [ ] 1.2 Keep the existing `get_download_link` path for `dir` resources and as a fallback for file resources without a `file` URL.

## 2. Tests

- [ ] 2.1 Add `TestFullSkipDuplicateApiCall` covering: file resource with `file` URL skips second call; file resource without it still calls `get_download_link`; directory resource always calls `get_download_link`.
- [ ] 2.2 All 96 existing tests still pass.

## 3. Validation

- [ ] 3.1 `pytest -q` passes.
- [ ] 3.2 `openspec validate skip-duplicate-full-api-call --strict` passes.