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

### Requirement: Coverage Is Reported And Enforced
CI MUST run pytest with `--cov=ydiskarc` and MUST fail the build if line coverage falls below the configured threshold (currently 70%).

#### Scenario: Coverage below threshold fails the build
- **WHEN** a commit drops coverage below the threshold
- **THEN** the `test` job exits non-zero
- **AND** the workflow fails the build.

#### Scenario: Coverage above threshold passes
- **WHEN** coverage is at or above the threshold
- **THEN** the `test` job produces a coverage report and uploads `coverage.xml` to Codecov.