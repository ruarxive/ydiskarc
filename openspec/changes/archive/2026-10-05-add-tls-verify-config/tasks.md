## 1. Implementation

- [ ] 1.1 Add `verify` field to `Config` in `ydiskarc/config.py` (default `None`, accept `bool | str | None`).
- [ ] 1.2 In `ydiskarc/downloader.py`, route `verify=config.verify` through `_probe` instead of hardcoding `True`.
- [ ] 1.3 Document `YDISKARC_TLS_VERIFY` env override in `README.md`.

## 2. Tests

- [ ] 2.1 Add `tests/test_config.py` covering default `None`, `True`, `False`, and `"/path/to/bundle"` settings.
- [ ] 2.2 Existing 79 tests still pass.

## 3. Validation

- [ ] 3.1 `pytest -q --cov=ydiskarc --cov-fail-under=70` passes.
- [ ] 3.2 `openspec validate add-tls-verify-config --strict` passes.