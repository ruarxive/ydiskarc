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

### Requirement: Tag-Triggered Release Workflow
Pushing a tag matching `v*.*.*` MUST trigger an automated GitHub Actions workflow that builds the sdist and wheel and publishes to PyPI via OIDC trusted publishing. No long-lived PyPI token is required.

#### Scenario: Tag push publishes to PyPI
- **WHEN** a maintainer pushes a tag like `v1.2.0`
- **THEN** the `release` workflow runs
- **AND** it uploads the new version to PyPI within minutes.

#### Scenario: Failed build aborts the publish
- **WHEN** the build step fails
- **THEN** the publish step is skipped
- **AND** no artifact is uploaded to PyPI.