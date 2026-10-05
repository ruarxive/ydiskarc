## MODIFIED Requirements

### Requirement: Modular Core Logic
The application logic MUST be split into single-responsibility modules rather than a monolithic `processor.py` file.

#### Scenario: Downloading a single file
- **WHEN** the CLI delegates the command
- **THEN** the `client.py` handles the Yandex API session
- **AND** the `downloader.py` handles the physical file streaming and progress bar.

### Requirement: Safe File Streaming
Downloads MUST write to a temporary `.part` file until fully downloaded to prevent corrupted files on interruption.

#### Scenario: Interrupted download
- **WHEN** a file is mid-download and the process is interrupted or fails
- **THEN** the partial file remains as `<filename>.part` and is not mistaken for a completed download.

### Requirement: CI Quality Gates Are Enforced
CI MUST treat every check (flake8, black, isort, ruff, mypy, pytest) as a build-breaking failure. No `|| true`, `continue-on-error: true`, or equivalent swallowing of failures is permitted in the CI workflow.

#### Scenario: Mypy regression fails the build
- **WHEN** a commit introduces a mypy regression
- **THEN** the `lint` job exits non-zero
- **AND** the workflow fails the build (status red).

#### Scenario: Stale Python targets are not in the matrix
- **WHEN** the test matrix is inspected
- **THEN** Python 3.8 and earlier MUST NOT appear
- **AND** the matrix MUST include the minimum supported version (`3.9`) and at least one newer version.

#### Scenario: Tooling versions match pyproject.toml
- **WHEN** the pre-commit mypy hook runs
- **THEN** it MUST target the minimum supported Python version declared in `pyproject.toml` (currently 3.9).