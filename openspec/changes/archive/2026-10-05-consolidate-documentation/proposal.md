## Why

Three documentation drifts identified in the audit:

1. `README.md:38` says "Python version 3.6 or greater is required" but `pyproject.toml` requires `>=3.9`.
2. `CHANGELOG.md` has the same set of changes duplicated under both `[1.1.0]` (lines 13–31) and `[Unreleased]` (lines 32–60).
3. `openspec/project.md` is the upstream OpenSpec template — every line is a placeholder.
4. `openspec/specs/core-architecture/spec.md` has a `## Purpose` line that says `TBD - created by archiving change refactor-architecture. Update Purpose after archive.`

## What Changes

- README: bump "Python 3.6+" → "Python 3.9+".
- CHANGELOG: keep the `[1.1.0]` block; replace `[Unreleased]` block with the items added since then (logging fix, path traversal, RFC 5987, configure command, __all__, CI hardening).
- `openspec/project.md`: fill in the template sections with real content (purpose, tech stack, conventions, testing, git workflow).
- `openspec/specs/core-architecture/spec.md`: replace `TBD` with a 1–2 sentence purpose.

## Capabilities

### Modified Capabilities
- `core-architecture`: Documentation must reflect the project's actual state (Python version, architecture, OpenSpec metadata).

## Impact

- Doc-only changes. No code or tests affected.
- README/CHANGELOG updates visible to users on PyPI.