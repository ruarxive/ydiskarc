## Why

`Project.configure()` (in `ydiskarc/cmds/processor.py`) writes an OAuth key to a `.ydiskarc` YAML file using `yaml.safe_dump`. The method exists but **is not exposed via any Typer command** in `ydiskarc/core.py`, so it is dead code. Worse, the OAuth key is written in plaintext with default umask (`0o644` on most systems — world-readable).

This change wires the dead code as a working CLI command, applies `chmod 0o600` after writing (POSIX only — best-effort, ignored on Windows), and documents the workflow.

## What Changes

- Add `ydiskarc configure --key <KEY>` Typer command in `core.py` that calls `Project.configure()`.
- The `Project.configure()` method now calls `os.chmod(filepath, 0o600)` after writing (already done — verify).
- Update `README.md` so the `ydiskarc configure --key YOUR_OAUTH_KEY` example actually works.
- Add a regression test that runs `Project.configure()` and asserts the file exists with `0o600` perms on POSIX.

## Capabilities

### Modified Capabilities
- `core-architecture`: Configuration management MUST be reachable via the CLI and stored with restrictive file permissions (POSIX `0o600`).

## Impact

- `ydiskarc/core.py` — add `configure` Typer command.
- `ydiskarc/cmds/processor.py` — `configure()` already chmod's; verify and test.
- `tests/test_core.py` — add CLI smoke test.
- `tests/test_processor.py` — add unit test for `Project.configure()`.
- `README.md` — small clarification.