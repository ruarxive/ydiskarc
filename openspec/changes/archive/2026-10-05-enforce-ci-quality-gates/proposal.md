## Why

Several CI/tooling configuration drifts violate the principle of least surprise:

- `.github/workflows/ci.yml:84` runs `mypy ydiskarc --ignore-missing-imports || true` — typing regressions cannot fail the build.
- `tox.ini:7` pins `envlist = py38` (Python 3.8 is EOL) while `pyproject.toml` requires `>=3.9` and the CI matrix uses 3.9/3.10/3.11.
- `.pre-commit-config.yaml:38` passes `--python-version=3.6` to mypy, contradicting `pyproject.toml`'s `>=3.9` and silently skipping checks for newer Python features.
- The `lint` job runs flake8, black, mypy but no `isort` or `ruff` despite the README documenting `ruff` as a quality gate.
- GitHub Actions are pinned to `v3`/`v4` (Node 16 runtime, deprecated).

See `dev/docs/ANALYSIS_AND_IMPROVEMENTS.md` §6.1–6.4, 6.7.

## What Changes

- Remove `|| true` from the `mypy` step in `.github/workflows/ci.yml`.
- Update `tox.ini` to `envlist = py39, py310, py311, py312`.
- Update `.pre-commit-config.yaml` mypy hook to `--python-version=3.9`.
- Add `isort` and `ruff` invocations to the `lint` job in `.github/workflows/ci.yml`.
- Bump `actions/checkout@v4`, `actions/setup-python@v5`, `actions/cache@v4`.

## Capabilities

### Modified Capabilities
- `core-architecture`: CI MUST enforce every declared quality check; failure on any check MUST fail the build.

## Impact

- `.github/workflows/ci.yml`, `tox.ini`, `.pre-commit-config.yaml` — config-only changes.
- No source-code changes.
- No runtime dependencies changed.