## 1. Implementation

- [ ] 1.1 Create `ydiskarc/constants.py` with file-system, HTTP, JSON-key, and default constants.
- [ ] 1.2 Replace `'_metadata.json'` and `'dump.zip'` literals in `ydiskarc/cmds/processor.py` with `constants.METADATA_FILENAME` and `constants.DEFAULT_FULL_FILENAME`.
- [ ] 1.3 Replace `'Content-Disposition'` and `'_embedded'`/`'items'`/`'path'`/`'type'`/`'size'`/`'file'`/`'dir'`/`'public_key'` literals across `downloader.py`, `processor.py`, `client.py`.
- [ ] 1.4 Replace `429` with `HTTP_TOO_MANY_REQUESTS` where it's compared (let urllib3 Retry's status_forcelist use the constant too).
- [ ] 1.5 Replace `limit=1000` with `limit=DEFAULT_API_LIST_LIMIT`.

## 2. Tests

- [ ] 2.1 Add `tests/test_constants.py` asserting the constants exist and are non-empty strings.
- [ ] 2.2 All existing 49 tests still pass.

## 3. Validation

- [ ] 3.1 `pytest -q` passes.
- [ ] 3.2 `flake8`, `black --check`, `isort --check-only` all clean.
- [ ] 3.3 `openspec validate extract-magic-constants --strict` passes.