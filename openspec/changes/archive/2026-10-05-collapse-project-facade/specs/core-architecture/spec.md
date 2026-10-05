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

### Requirement: Project Facade Is The Single Entry Point
Recursive walk logic (`yd_get_full`, `yd_get_and_store_dir`, `scan_directory_for_stats`) MUST live only as private helpers inside `ydiskarc.cmds.processor`. The `Project` class is the only public API for these operations.

#### Scenario: Direct helper import is impossible
- **WHEN** code attempts `from ydiskarc.cmds.processor import yd_get_and_store_dir`
- **THEN** an `ImportError` is raised.

#### Scenario: Project is the public surface
- **WHEN** the `sync` Typer command runs
- **THEN** it MUST reach `yd_get_and_store_dir` only through `Project.sync(...)`.

#### Scenario: Wildcard import is constrained
- **WHEN** a user runs `from ydiskarc.cmds.processor import *`
- **THEN** only `PathTraversalError`, `Project`, and `safe_join` are imported (as declared in `__all__`).