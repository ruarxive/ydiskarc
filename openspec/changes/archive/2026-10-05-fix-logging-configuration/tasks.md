## 1. Implementation

- [ ] 1.1 Define a module-level logger constant in `ydiskarc/core.py` (e.g. `LOGGER_NAME = "ydiskarc"`).
- [ ] 1.2 Rewrite `setup_logging(verbose: bool)` to attach a `StreamHandler` only when `verbose=True`, set the level on the namespaced logger, and never call `logging.basicConfig` or `logging.disable`.
- [ ] 1.3 Add a regression test in `tests/test_core.py` that calls `setup_logging(True)`, captures stderr via `caplog`/`capfd`, and asserts a ydiskarc log line is emitted.
- [ ] 1.4 Add a regression test that calls `setup_logging(False)` and asserts no ydiskarc `INFO`/`DEBUG` line is emitted.

## 2. Validation

- [ ] 2.1 `pytest tests/test_core.py -q` passes.
- [ ] 2.2 `pytest -q` (full suite) passes (20 existing tests + new ones).
- [ ] 2.3 Manual smoke: `python -c "import ydiskarc.core; ydiskarc.core.setup_logging(True); import logging; logging.getLogger('ydiskarc').info('hi')"` prints `hi`.