## 1. Implementation

- [ ] 1.1 Rename `yd_get_full` → `_yd_get_full` in `ydiskarc/cmds/processor.py`.
- [ ] 1.2 Rename `yd_get_and_store_dir` → `_yd_get_and_store_dir`.
- [ ] 1.3 Rename `scan_directory_for_stats` → `_scan_directory_for_stats`.
- [ ] 1.4 Update internal call sites (Project.full / Project.sync / Project.__store).
- [ ] 1.5 Add `__all__ = ["PathTraversalError", "Project", "safe_join"]` to `processor.py`.
- [ ] 1.6 Update `ydiskarc/cmds/__init__.py` to import only `Project`.

## 2. Tests

- [ ] 2.1 Update `tests/test_processor.py` to import from `Project` where it currently imports the module-level helpers.
- [ ] 2.2 Existing 92 tests still pass.

## 3. Validation

- [ ] 3.1 `pytest -q` passes.
- [ ] 3.2 `openspec validate collapse-project-facade --strict` passes.