## Why

`Project` (in `ydiskarc/cmds/processor.py`) is a thin pass-through: `Project.sync()` calls `self.__store()` which calls `yd_get_and_store_dir()`; `Project.full()` calls `yd_get_full()`. The class adds no behavior but doubles the call surface. The Typer commands in `core.py` create a `Project` and immediately delegate, while the rest of `cmds/processor.py` exposes the underlying helpers at module level.

This change makes `Project` the **single** entry point: the module-level helpers become private (`_yd_get_full`, `_yd_get_and_store_dir`, `_scan_directory_for_stats`) and only `Project` exposes the public surface.

## What Changes

- Rename `yd_get_full` → `_yd_get_full`, `yd_get_and_store_dir` → `_yd_get_and_store_dir`, `scan_directory_for_stats` → `_scan_directory_for_stats`.
- Promote `safe_join` and `PathTraversalError` to module-public (they're already public via tests).
- `Project.full`, `Project.sync` continue to delegate — but now they're the only public entry into the recursive walker logic.
- Update tests to import from `Project` where appropriate.
- Add an `__all__` to `ydiskarc/cmds/processor.py`.

## Capabilities

### Modified Capabilities
- `core-architecture`: The recursive walk logic MUST be reachable only through the `Project` facade.

## Impact

- `ydiskarc/cmds/processor.py` — rename three functions, add `__all__`.
- `tests/test_processor.py` — update imports.
- `ydiskarc/cmds/__init__.py` — `Project` only.