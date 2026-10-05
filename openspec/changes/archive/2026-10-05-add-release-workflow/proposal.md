## Why

There is no automated release workflow. Tagging a commit requires a developer to manually run `python -m build` and `twine upload`, with the OAuth key in their local `.pypirc`. This is error-prone and slow. Adding a tag-triggered GitHub Actions workflow that builds the sdist/wheel and publishes to PyPI via OIDC trusted publishing removes the manual step.

## What Changes

- Add `.github/workflows/release.yml` that triggers on tags matching `v*.*.*` (e.g. `v1.2.0`).
- Steps: checkout → set up Python → install build → build sdist + wheel → publish to PyPI via `pypa/gh-action-pypi-publish` (OIDC trusted publishing).
- Document the trusted-publishing setup in `README.md` and `CONTRIBUTING.rst` (the latter does not exist; we'll create a short CONTRIBUTING section inside README).

## Capabilities

### Modified Capabilities
- `core-architecture`: Project MUST publish to PyPI via an automated tag-triggered workflow using OIDC trusted publishing (no long-lived API token).

## Impact

- New file `.github/workflows/release.yml`.
- `README.md` — short section on releasing.
- No source-code changes.