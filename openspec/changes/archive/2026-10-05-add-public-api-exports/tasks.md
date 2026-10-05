## 1. Implementation

- [ ] 1.1 Add `__all__ = ["__version__", "__author__", "__licence__"]` to `ydiskarc/__init__.py`.
- [ ] 1.2 Add `__all__ = ["Project"]` to `ydiskarc/cmds/__init__.py` and import `Project` from `ydiskarc.cmds.processor`.
- [ ] 1.3 Add `__all__ = ["YandexDiskClient"]` to `ydiskarc/client.py`.
- [ ] 1.4 Add `__all__ = ["ResourceDownloader", "format_size"]` to `ydiskarc/downloader.py`.
- [ ] 1.5 Add `__all__ = ["ResourceItem", "ResourceList", "ResourceInfo"]` to `ydiskarc/models.py`.

## 2. Tests

- [ ] 2.1 Add `tests/test_exports.py` asserting `from ydiskarc import *` produces the expected names (use a controlled `__import__` or `dir()` filter).
- [ ] 2.2 Existing tests pass without modification.

## 3. Validation

- [ ] 3.1 `pytest -q` passes.
- [ ] 3.2 `openspec validate add-public-api-exports --strict` passes.