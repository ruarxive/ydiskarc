## Why

`requirements.txt` and `requirements-dev.txt` pin lower bounds but no upper bounds, and no automated tooling updates them. Recent CVEs in `requests`/`urllib3` (e.g. CVE-2024-35195) and PyYAML would silently slip through. There is no Dependabot / Renovate config and no SCA scan in CI.

## What Changes

- Add `.github/dependabot.yml` configuring Dependabot for:
  - `pip` ecosystem (weekly updates for `requirements.txt`, `requirements-dev.txt`, and the `pyproject.toml` `[project.dependencies]` group).
  - `github-actions` ecosystem (weekly updates for `.github/workflows/*.yml`).
- Add a `pip-audit` SCA job to CI that runs on every push to `main` and on PRs.

## Capabilities

### Modified Capabilities
- `core-architecture`: Dependencies MUST be tracked by Dependabot and CI MUST run `pip-audit` (or equivalent) to detect known vulnerabilities.

## Impact

- New file `.github/dependabot.yml`.
- New job `sca` in `.github/workflows/ci.yml` invoking `pip-audit`.
- Documentation-only change in `README.md` to mention dependency policy.
- No source-code changes.