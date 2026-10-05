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

### Requirement: Named Constants for Repeated Literals
Repeating string and number literals MUST be defined as named constants in a single `ydiskarc/constants.py` module rather than duplicated across call sites.

#### Scenario: Metadata filename constant
- **WHEN** `yd_get_and_store_dir` writes the per-directory metadata sidecar
- **THEN** it MUST use `constants.METADATA_FILENAME`, not the literal `'_metadata.json'`.

#### Scenario: Yandex JSON keys are named
- **WHEN** the recursive walker inspects API responses
- **THEN** it MUST use `constants.JSON_EMBEDDED`, `constants.JSON_ITEMS`, `constants.JSON_PATH`, `constants.JSON_TYPE`, `constants.JSON_SIZE`, `constants.JSON_FILE` instead of literal strings.

#### Scenario: HTTP status constants
- **WHEN** the rate-limit helper compares the response status code
- **THEN** it MUST use `constants.HTTP_TOO_MANY_REQUESTS` (= 429), not the literal `429`.