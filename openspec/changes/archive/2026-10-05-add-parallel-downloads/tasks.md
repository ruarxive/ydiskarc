## 1. Implementation

- [ ] 1.1 Add `pool_maxsize: int = 10` to `Config`; pass it to `HTTPAdapter(pool_connections=pool_maxsize, pool_maxsize=pool_maxsize)`.
- [ ] 1.2 Add `parallel: int = 1` parameter to `yd_get_and_store_dir` (and `scan_directory_for_stats` if needed).
- [ ] 1.3 In `yd_get_and_store_dir`, when iterating files and `parallel > 1`, dispatch to a `ThreadPoolExecutor(max_workers=parallel)`.
- [ ] 1.4 Add `--parallel` option to the `sync` Typer command; default `1`.
- [ ] 1.5 Document `--parallel` in `README.md`.

## 2. Tests

- [ ] 2.1 Add `tests/test_parallel.py` that a `parallel=4` invocation submits 4 download calls for a 4-item listing.
- [ ] 2.2 Existing 89 tests still pass.

## 3. Validation

- [ ] 3.1 `pytest -q --cov=ydiskarc --cov-fail-under=70` passes.
- [ ] 3.2 `openspec validate add-parallel-downloads --strict` passes.