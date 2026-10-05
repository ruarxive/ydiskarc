## 1. Implementation

- [ ] 1.1 Add `@app.command("configure")` to `ydiskarc/core.py` accepting `--key` (and optionally `--projectdir`).
- [ ] 1.2 Verify `Project.configure()` already chmod's the file to 0o600; confirm test.
- [ ] 1.3 Update `README.md` so the `ydiskarc configure --key YOUR_OAUTH_KEY` example references the now-exposed command.

## 2. Tests

- [ ] 2.1 Add `tests/test_processor.py::test_project_configure_writes_file_with_restricted_perms` that runs `Project().configure("test-key", projectdir=tmp_path)` and asserts (a) the file exists, (b) it contains the key, (c) on POSIX, mode bits are 0o600.
- [ ] 2.2 Add `tests/test_core.py::test_configure_command_exists` that invokes `app` and verifies the command is registered.

## 3. Validation

- [ ] 3.1 `pytest -q` passes.
- [ ] 3.2 `openspec validate resolve-configure-cmd --strict` passes.