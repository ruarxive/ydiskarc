## Why

None of the `ydiskarc` modules declare `__all__`. Consumers (`from ydiskarc import *`, type-checkers, IDE auto-import, `help(ydiskarc)`) have no reliable signal for which symbols are public. The empty `ydiskarc/cmds/__init__.py` is particularly confusing: `from ydiskarc.cmds import Project` works, but `from ydiskarc.cmds import *` is a no-op despite `Project` being a usable class.

See `dev/docs/ANALYSIS_AND_IMPROVEMENTS.md` headline #5 and §3 of the action plan.

## What Changes

- Add `__all__` to `ydiskarc/__init__.py` listing `__version__`, `__author__`, `__licence__`.
- Add `__all__` to `ydiskarc/cmds/__init__.py` re-exporting `Project`.
- Add `__all__` to `ydiskarc/client.py` re-exporting `YandexDiskClient`.
- Add `__all__` to `ydiskarc/downloader.py` re-exporting `ResourceDownloader`, `format_size`.
- Add `__all__` to `ydiskarc/models.py` re-exporting `ResourceItem`, `ResourceList`, `ResourceInfo`.

## Capabilities

### Modified Capabilities
- `core-architecture`: Each module MUST define `__all__` so the public API surface is unambiguous.

## Impact

- `ydiskarc/__init__.py`, `ydiskarc/cmds/__init__.py`, `ydiskarc/client.py`, `ydiskarc/downloader.py`, `ydiskarc/models.py` — pure declarations, no behavior change.
- No public-API breakage (only adds documentation).
- No runtime dependencies changed.