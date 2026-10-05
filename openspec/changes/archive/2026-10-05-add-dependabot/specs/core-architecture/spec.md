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

### Requirement: Automated Dependency Tracking
The project MUST have a `.github/dependabot.yml` configuration that enables weekly dependency updates for the `pip` and `github-actions` ecosystems. CI MUST run a software composition analysis (`pip-audit`) step on every push and pull request.

#### Scenario: Dependabot opens a weekly PR
- **WHEN** Dependabot detects an outdated dependency in `requirements.txt`
- **THEN** it opens a pull request that CI MUST validate.

#### Scenario: pip-audit detects a CVE
- **WHEN** a dependency has a known CVE
- **THEN** the `sca` CI job exits non-zero
- **AND** the workflow fails the build.