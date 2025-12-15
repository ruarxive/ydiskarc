# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2021-11-26

### Added
- First public release on PyPI and updated github code

## [1.1.0] - 2025-12-15

### Changed
- **BREAKING**: Changed URL from option (`--url`) to positional argument for `sync` and `full` commands
- Replaced Rich progress bars with tqdm for better compatibility and performance
- Made logging conditional - logs only appear when `--verbose` flag is used
- Changed default output filename for `full` command to `dump.zip` instead of auto-detected name

### Added
- **Progress bars with tqdm** - Visual progress indicators for file downloads
- **Pre-download statistics** - Shows total file count and estimated size before downloading
- **Examples directory** - Added example metadata file and comprehensive documentation
- **Metadata structure documentation** - Detailed documentation of Yandex.Disk API metadata format

### Fixed
- All linting issues (flake8, ruff, black, isort)
- Type annotation issues
- Code formatting and style consistency

## [Unreleased]

### Changed
- Migrated CLI framework from Click to Typer for better type hints and modern Python support
- Improved logging with better formatting and debug levels
- Enhanced error handling and user feedback
- **BREAKING**: Changed URL from option (`--url`) to positional argument for `sync` and `full` commands
- Replaced Rich progress bars with tqdm for better compatibility and performance
- Made logging conditional - logs only appear when `--verbose` flag is used
- Changed default output filename for `full` command to `dump.zip` instead of auto-detected name

### Added
- Rich library integration for better terminal output and progress indicators
- Verbose mode (`-v`/`--verbose`) for detailed logging
- Better error messages and exception handling
- Metadata extraction improvements
- **Progress bars with tqdm** - Visual progress indicators for file downloads
- **Pre-download statistics** - Shows total file count and estimated size before downloading
- **Examples directory** - Added example metadata file and comprehensive documentation
- **Metadata structure documentation** - Detailed documentation of Yandex.Disk API metadata format

### Fixed
- Security vulnerabilities in YAML loading
- CLI option conflicts
- Progress bar display issues
- Various code quality improvements
- All linting issues (flake8, ruff, black, isort)
- Type annotation issues
- Code formatting and style consistency
