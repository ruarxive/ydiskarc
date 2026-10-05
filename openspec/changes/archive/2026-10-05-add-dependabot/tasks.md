## 1. Implementation

- [ ] 1.1 Create `.github/dependabot.yml` with weekly pip + github-actions updates.
- [ ] 1.2 Add `pip-audit` step to `.github/workflows/ci.yml` (run after tests).
- [ ] 1.3 Add `pip-audit` to `requirements-dev.txt`.

## 2. Documentation

- [ ] 2.1 Add a short "Security & dependency updates" section to `README.md`.

## 3. Validation

- [ ] 3.1 `pip-audit` reports no critical/high findings for current lockfile (locally).
- [ ] 3.2 `openspec validate add-dependabot --strict` passes.