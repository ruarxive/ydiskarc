# core-architecture Specification

## Purpose

Defines the high-level structure of the ydiskarc codebase: how the CLI
(`core.py`) delegates to focused modules (`client.py`, `downloader.py`,
`models.py`, `config.py`, `constants.py`), the safety invariants that must
hold (`.part` files, path traversal containment, package-scoped logging), and
the public API surface (`__all__` declarations).

## Requirements
### Requirement: Modular Core Logic
The application logic MUST be split into single-responsibility modules rather than a monolithic `processor.py` file.
#### Scenario: Downloading a single file
Given the user requests to download a single file
When the CLI delegates the command
Then the `client.py` handles the Yandex API session
And the `downloader.py` handles the physical file streaming and progress bar.

### Requirement: Safe File Streaming
Downloads MUST write to a temporary `.part` file until fully downloaded to prevent corrupted files on interruption.
#### Scenario: Interrupted download
Given a file is mid-download
When the process is interrupted or fails
Then the partial file remains as `<filename>.part` and is not mistaken for a completed download.

