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

### Requirement: Avoid Duplicate API Call For Single-File Resources
When `full` is invoked on a single-file public resource, the implementation MUST issue at most one API call before downloading. The `get_download_link` endpoint MUST be called only as a fallback when the metadata response lacks a usable direct URL.

#### Scenario: Single-file resource with `file` URL in metadata
- **WHEN** `_yd_get_full` runs against `https://disk.yandex.ru/i/...`
- **AND** the metadata response is `{"type": "file", "file": "https://...", "size": N}`
- **THEN** the second API call (`get_download_link`) is skipped
- **AND** the downloader receives the `file` URL directly.

#### Scenario: Single-file resource without `file` URL
- **WHEN** the metadata response is `{"type": "file"}` (no `file` URL)
- **THEN** `_yd_get_full` MUST fall back to `get_download_link`.

#### Scenario: Directory resource
- **WHEN** the metadata response is `{"type": "dir"}`
- **THEN** `_yd_get_full` MUST call `get_download_link` (which returns the ZIP archive URL).