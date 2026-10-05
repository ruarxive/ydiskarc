## Why

CI currently runs `pytest` without coverage. The `.coveragerc` file declares `source = ydiskarc` but it is never invoked. There is no coverage badge, no threshold enforcement, no Codecov upload.

## What Changes

- Add `pytest-cov` to `requirements-dev.txt`.
- Update CI to run `pytest --cov=ydiskarc --cov-report=xml --cov-report=term`.
- Add `--cov-fail-under=85` to enforce a minimum coverage threshold.
- Add a Codecov badge to `README.md`.

## Capabilities

### Modified Capabilities
- `core-architecture`: CI MUST report test coverage and enforce a minimum threshold.

## Impact

- `requirements-dev.txt` — add `pytest-cov`.
- `.github/workflows/ci.yml` — invoke pytest with `--cov` flags.
- `README.md` — add Codecov badge.
- No source-code changes.