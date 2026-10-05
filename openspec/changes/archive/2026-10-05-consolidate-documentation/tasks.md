## 1. Documentation

- [ ] 1.1 Fix `README.md:38` — replace "Python 3.6 or greater" with "Python 3.9 or greater".
- [ ] 1.2 Clean `CHANGELOG.md`: keep the `[1.1.0]` block as the most recent release; replace `[Unreleased]` with a list of the changes this audit brought in (logging fix, path traversal, RFC 5987, configure command, `__all__`, CI hardening, dedupe-rate-limit, constants module, coverage, etc.).
- [ ] 1.3 Fill in `openspec/project.md` with real content.
- [ ] 1.4 Replace `TBD - created by archiving change...` in `openspec/specs/core-architecture/spec.md` with a real Purpose sentence.

## 2. Validation

- [ ] 2.1 `openspec validate consolidate-documentation --strict` passes.
- [ ] 2.2 `pytest -q` still passes (doc-only change, no regression risk).