## 1. Implementation

- [ ] 1.1 Add `pytest-cov` to `requirements-dev.txt`.
- [ ] 1.2 Update `.github/workflows/ci.yml` test job to run `pytest --cov=ydiskarc --cov-report=xml --cov-report=term --cov-fail-under=70`.
- [ ] 1.3 Add a Codecov upload step (using `codecov/codecov-action@v4`).

## 2. Documentation

- [ ] 2.1 Add Codecov badge to `README.md`.

## 3. Validation

- [ ] 3.1 `pytest -q --cov=ydiskarc --cov-fail-under=85` passes locally.
- [ ] 3.2 `openspec validate add-coverage-reporting --strict` passes.