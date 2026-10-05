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

### Requirement: Explicit Public API Surface
Every ydiskarc module MUST define `__all__` listing its public symbols. Wildcard imports MUST yield only those symbols.

#### Scenario: Importing the package
- **WHEN** a user runs `from ydiskarc import *`
- **THEN** only `__version__`, `__author__`, `__licence__` are bound (or are excluded by `__all__`'s explicit list).

#### Scenario: Importing the cmds submodule
- **WHEN** a user runs `from ydiskarc.cmds import *`
- **THEN** `Project` is bound in the caller's scope.

#### Scenario: Importing client or downloader
- **WHEN** a user runs `from ydiskarc import client` / `from ydiskarc import downloader`
- **THEN** the documented class and helper functions are bound, and no internal helpers leak into the public namespace.