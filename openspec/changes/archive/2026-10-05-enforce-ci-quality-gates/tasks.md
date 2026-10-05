## 1. CI workflow

- [ ] 1.1 In `.github/workflows/ci.yml`, change `mypy ydiskarc --ignore-missing-imports || true` to `mypy ydiskarc --ignore-missing-imports` (drop `|| true`).
- [ ] 1.2 In `.github/workflows/ci.yml`, bump `actions/checkout@v3` → `@v4`, `actions/setup-python@v4` → `@v5`, `actions/cache@v3` → `@v4`.
- [ ] 1.3 Add `isort --check-only --profile black --line-length 100 ydiskarc tests` and `ruff check ydiskarc tests` steps to the `lint` job.
- [ ] 1.4 Install `isort` and `ruff` in the `Install linting tools` step.

## 2. Tox

- [ ] 2.1 In `tox.ini`, change `envlist = py38` → `envlist = py39, py310, py311, py312`.

## 3. Pre-commit

- [ ] 3.1 In `.pre-commit-config.yaml`, change `--python-version=3.6` → `--python-version=3.9` in the mypy hook args.

## 4. Validation

- [ ] 4.1 `tox -e py311` passes locally.
- [ ] 4.3 `pre-commit run --all-files` (if installed) passes locally.
- [ ] 4.4 `openspec validate enforce-ci-quality-gates --strict` passes.