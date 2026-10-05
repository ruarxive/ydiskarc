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

### Requirement: RFC 6266 / 5987 Filename Parsing
Filenames derived from server-supplied `Content-Disposition` headers MUST follow RFC 6266 / 5987. When both `filename=` and `filename*=` are supplied, `filename*=` takes precedence. The parsed name MUST be sanitized (no control characters, no path separators) before being used as a local filename.

#### Scenario: RFC 5987 utf-8 filename
- **WHEN** the header is `attachment; filename*=UTF-8''%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80.pdf`
- **THEN** the helper decodes to `Пример.pdf`.

#### Scenario: filename* preferred over filename
- **WHEN** the header contains both `filename=fallback.pdf` and `filename*=UTF-8''actual.pdf`
- **THEN** the helper returns `actual.pdf`, not `fallback.pdf`.

#### Scenario: missing header
- **WHEN** no `Content-Disposition` header is present
- **THEN** the helper returns `None` and the caller falls back to the URL tail.

#### Scenario: header-injection attempt
- **WHEN** the header contains CR/LF or path separators
- **THEN** the helper strips or replaces them before returning, so the value is safe to use as a local filename.