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

### Requirement: Configurable TLS Verification
The TLS verification mode MUST be configurable through `Config.verify` and the `YDISKARC_TLS_VERIFY` environment variable. The default (`None`) MUST preserve current behavior (verify against system trust store).

#### Scenario: Default behavior unchanged
- **WHEN** neither `Config.verify` nor `YDISKARC_TLS_VERIFY` is set
- **THEN** requests use the system trust store (`verify=True`).

#### Scenario: Custom CA bundle
- **WHEN** `YDISKARC_TLS_VERIFY=/etc/pki/my-ca.pem` (or `Config.verify` is set to a path)
- **THEN** requests use the supplied CA bundle.

#### Scenario: Disable verification
- **WHEN** `YDISKARC_TLS_VERIFY=0` (or `Config.verify=False`)
- **THEN** requests skip verification (with a printed warning).