## 1. Implementation

- [ ] 1.1 Add `safe_join(base, *parts)` helper to `ydiskarc/cmds/processor.py` (realpath both sides, raise `ValueError` on escape).
- [ ] 1.2 Replace the four `os.path.join(*arr)` sites (lines ~107, 137, 154, 170) with `safe_join(output, *row["path"].split("/"))` calls.
- [ ] 1.3 Surface `ValueError` from `safe_join` cleanly: log via `logging.warning` (not `print`) when `verbose=True`, otherwise silently skip the offending item and continue.

## 2. Tests

- [ ] 2.1 Add `tests/test_processor.py::test_path_traversal_blocked` that mocks the API to return `{"path": "../../etc/passwd", ...}` and asserts `ValueError` is raised by the recursive walk.
- [ ] 2.2 Add `test_safe_join_allows_normal_nested` (sanity test for legitimate paths like `"/dir1/dir2"`).
- [ ] 2.3 Add `test_safe_join_rejects_absolute` (a path starting with `/`).

## 3. Validation

- [ ] 3.1 `pytest -q` passes (20 existing + new tests).
- [ ] 3.2 `openspec validate fix-path-traversal --strict` passes.