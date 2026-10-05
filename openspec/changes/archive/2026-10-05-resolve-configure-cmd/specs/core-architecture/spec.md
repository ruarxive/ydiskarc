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

### Requirement: Reachable Configure Command
A `ydiskarc configure --key <KEY>` command MUST exist and write the OAuth key to `.ydiskarc` with `0o600` POSIX permissions.

#### Scenario: configure writes the file
- **WHEN** the user runs `ydiskarc configure --key abc`
- **THEN** a `.ydiskarc` YAML file is created in the working directory (or specified `--projectdir`)
- **AND** the file contains `keys.yandex_oauth: abc`
- **AND** the file's POSIX mode bits are `0o600` (best-effort; on Windows the call is silently skipped).

#### Scenario: configure preserves existing config
- **WHEN** an existing `.ydiskarc` is present
- **THEN** `configure --key X` MUST update only the `keys.yandex_oauth` field
- **AND** any other keys MUST be preserved.