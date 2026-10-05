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

### Requirement: Per-Package Logging Configuration
The CLI MUST configure logging only for the `ydiskarc` package logger and MUST NOT call `logging.basicConfig` or `logging.disable` (which mutate process-global state).

#### Scenario: Verbose flag emits ydiskarc logs
- **WHEN** the user passes `-v` / `--verbose`
- **THEN** a `StreamHandler` is attached to the `ydiskarc` logger at `DEBUG` level
- **AND** log records from any `ydiskarc.*` module appear on stderr in human-readable form.

#### Scenario: Default mode is quiet
- **WHEN** the user does not pass `-v`
- **THEN** no `StreamHandler` is attached to the `ydiskarc` logger
- **AND** log records from `ydiskarc.*` at `INFO`/`DEBUG` are suppressed.

#### Scenario: Other libraries are not muted
- **WHEN** the user runs `ydiskarc sync URL` (no `-v`)
- **THEN** `logging.getLogger("urllib3").warning(...)` (or any other non-ydiskarc logger) MUST still reach its configured handler because no global `logging.disable` was called.