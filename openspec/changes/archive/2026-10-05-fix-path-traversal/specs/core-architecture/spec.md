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

### Requirement: Confined Output Paths
Local filesystem paths constructed from API-supplied `path` values MUST be confined to the user-specified output directory. Any path component that would resolve outside that directory MUST raise `ValueError` and skip the offending item.

#### Scenario: Normal nested path is allowed
- **WHEN** the API returns `path: "/SubDir/file.pdf"`
- **THEN** the helper resolves to `<output-dir>/SubDir/file.pdf` without error.

#### Scenario: Directory traversal is rejected
- **WHEN** the API returns `path: "../../etc/passwd"`
- **THEN** the helper raises `ValueError` containing "traversal" or "escapes" and the file is skipped (not partially written).

#### Scenario: Absolute path component is rejected
- **WHEN** a part begins with `/` (e.g. `"/etc/passwd"`)
- **THEN** the helper raises `ValueError`.