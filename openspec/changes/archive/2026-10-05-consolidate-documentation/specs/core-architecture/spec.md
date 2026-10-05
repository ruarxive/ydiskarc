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

### Requirement: Documentation Reflects Reality
User-facing documentation MUST accurately reflect the project's supported Python version, recent changes, and architecture.

#### Scenario: README Python version
- **WHEN** a user reads the installation section of `README.md`
- **THEN** the stated Python version MUST match `pyproject.toml`'s `requires-python` (currently `>=3.9`).

#### Scenario: OpenSpec Purpose is filled in
- **WHEN** `openspec/specs/core-architecture/spec.md` is opened
- **THEN** the `## Purpose` section MUST contain a non-placeholder sentence describing the capability.

#### Scenario: CHANGELOG has no duplicate entries
- **WHEN** the same change appears in `CHANGELOG.md`
- **THEN** it MUST appear exactly once (under its release version or `[Unreleased]`).