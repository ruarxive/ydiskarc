## Why

The `setup_logging` helper in `ydiskarc/core.py` is broken in two ways:

1. `setup_logging(verbose=False)` calls `logging.disable(logging.CRITICAL)`, a **process-global override** that mutes every downstream library (`urllib3`, `requests`, third-party plugins) for the rest of the process. The disable is sticky until the process exits and is not reversible from `setup_logging` itself.

2. `setup_logging(verbose=True)` calls `logging.basicConfig(...)`, which is a **silent no-op** once anything in the import graph (pytest plugin, IDE shim, or `tqdm`/`urllib3` initialization) has touched logging. Empirically verified: a second `basicConfig` call does not change the effective level.

The result is that `-v` is silently ineffective on real-world installations, and the default-quiet path breaks any third-party library that wants to log a warning. See `dev/docs/ANALYSIS_AND_IMPROVEMENTS.md` §Bug 1 and §Bug 2.

## What Changes

- Replace `setup_logging` with a namespaced logger approach (`ydiskarc` package logger + `NullHandler` default, `StreamHandler` only when `-v`).
- Stop calling `logging.disable` entirely; the project's own quietness is enforced by *not attaching handlers* and by leaving the logger's effective level at `WARNING`/`ERROR`.
- Preserve the existing UX: `-v` still produces human-readable log lines on stderr; absence of `-v` still suppresses ydiskarc's own logs without affecting other libraries.
- Add a unit test that verifies `-v` actually produces output.

## Capabilities

### Modified Capabilities
- `core-architecture`: Logging must be configurable per-package without leaking into process-global state.

## Impact

- `ydiskarc/core.py` — rewrite `setup_logging`.
- `tests/test_core.py` — add `test_verbose_logging_emits` regression test.
- No public-API breakage (no exports added or removed).
- No runtime dependencies changed.