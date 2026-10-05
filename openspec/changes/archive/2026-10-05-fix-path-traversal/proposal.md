## Why

`ydiskarc/cmds/processor.py` constructs local paths by joining API-supplied `path` values directly into `os.path.join(output, *parts)` in four places (`scan_directory_for_stats` lines 107–111, `yd_get_and_store_dir` lines 137–139, 154–156, 170–173). The API value is untrusted: a buggy or hostile Yandex.Disk response containing `..` segments, absolute paths, or other escape sequences would write or read outside the user's output directory.

Today the only mitigation is a vague `if "path" not in row: continue` check. There is no normalization, no `realpath` containment check, and no error surfaced to the caller when traversal is detected. See `dev/docs/ANALYSIS_AND_IMPROVEMENTS.md` §Bug 3.

## What Changes

- Add a single `safe_join(base: str, *parts: str) -> str` helper to `ydiskarc/cmds/processor.py` (or to a new `ydiskarc/paths.py` module) that:
  1. Strips whitespace and empty segments from each part.
  2. Joins them with `os.path.join`.
  3. Resolves with `os.path.realpath` against a realpathed base.
  4. Raises `ValueError` if the result is not contained in the base directory.
- Route every existing `os.path.join(*arr)` site through `safe_join`.
- Add a regression test that feeds a crafted API response with `path="../../etc/passwd"` and asserts `ValueError`.

## Capabilities

### Modified Capabilities
- `core-architecture`: File-system writes derived from external input MUST be confined to a user-chosen output directory.

## Impact

- `ydiskarc/cmds/processor.py` — add `safe_join`, replace four inline path constructions.
- `tests/test_processor.py` — add `test_path_traversal_blocked`.
- No public-API breakage (the helper is internal).
- No runtime dependencies changed.