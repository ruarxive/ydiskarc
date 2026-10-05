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

### Requirement: Centralized HTTP Retry Logic
Rate-limit (`429`) handling MUST be implemented in a single helper on `YandexDiskClient`. Each GET site MUST delegate to that helper rather than inline the `if status_code == 429: sleep; retry` pattern.

#### Scenario: 429 followed by 200
- **WHEN** the API returns 429 once
- **THEN** the helper waits for `Retry-After` and reissues the request
- **AND** the second response is returned to the caller with `raise_for_status()` already applied.

#### Scenario: 429 twice
- **WHEN** the API returns 429 twice
- **THEN** the helper propagates the second 429 response to the caller (after `raise_for_status()`).

#### Scenario: Initial 200
- **WHEN** the API returns 200 immediately
- **THEN** the helper returns the response without sleeping or reissuing.