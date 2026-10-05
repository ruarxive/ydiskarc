## 1. Implementation

- [ ] 1.1 Add `_parse_content_disposition(header_value: str) -> Optional[str]` to `ydiskarc/downloader.py`. Use `email.message.Message` for parsing; prefer `filename*` over `filename`; sanitize the result.
- [ ] 1.2 Add `_sanitize_filename(name: str) -> str` that strips control chars, replaces path separators with `_`, and strips leading/trailing whitespace.
- [ ] 1.3 Replace the inline regex in `get_file` with a call to the new helper.

## 2. Tests

- [ ] 2.1 Add `tests/test_downloader_helpers.py` with cases for: plain ASCII `filename=`, RFC 5987 `filename*=UTF-8''...`, both present (prefer `filename*`), missing header (returns None), quoted filename with embedded spaces, header with CR/LF attempt.
- [ ] 2.2 Existing 59 tests still pass.

## 3. Validation

- [ ] 3.1 `pytest -q` passes.
- [ ] 3.2 `openspec validate harden-content-disposition-parsing --strict` passes.