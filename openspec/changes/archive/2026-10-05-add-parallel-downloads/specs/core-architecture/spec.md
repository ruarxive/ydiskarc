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

### Requirement: Parallel File Downloads
The `sync` command MUST accept `--parallel N` to download files concurrently via a thread pool. Default `N=1` preserves current sequential behavior.

#### Scenario: parallel=1 is sequential
- **WHEN** the user runs `ydiskarc sync URL --parallel 1`
- **THEN** files are downloaded one at a time (unchanged behavior).

#### Scenario: parallel=4 dispatches concurrently
- **WHEN** the user runs `ydiskarc sync URL --parallel 4`
- **THEN** up to 4 file downloads run concurrently via a `ThreadPoolExecutor`
- **AND** the HTTP connection pool is large enough that workers don't share TCP connections.

#### Scenario: parallel greater than file count is safe
- **WHEN** `--parallel 8` is used with a 3-file resource
- **THEN** the executor runs at most 3 workers in flight; no error is raised.