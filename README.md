# ydiskarc

ydiskarc (pronounced *Ai-disk-arc*) is a command line tool used to backup Yandex.Disk public resources.
Public resources are only shared files and folders from Yandex.Disk service.
Yandex provides a free-to-use API that allows downloading the data.

[![CI](https://github.com/ruarxive/ydiskarc/actions/workflows/ci.yml/badge.svg)](https://github.com/ruarxive/ydiskarc/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ruarxive/ydiskarc/branch/main/graph/badge.svg)](https://codecov.io/gh/ruarxive/ydiskarc)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Dependabot](https://img.shields.io/badge/dependabot-enabled-brightgreen?logo=dependabot)](https://github.com/ruarxive/ydiskarc/network/dependencies)

## Main features

* **Metadata extraction** — automatically saves metadata as `_metadata.json` files.
* **Download any public resource** — single files or entire directory trees.
* **Resume support** — interrupted downloads continue from the last byte (`.part` files).
* **Retry logic** — transient network failures are handled automatically with exponential backoff.
* **Rate limiting handling** — the tool waits and retries on `429 Too Many Requests`.
* **Parallel transfer** — `--parallel N` dispatches file downloads through a thread pool.
* **Progress tracking** — visual progress bars for downloads via `tqdm`.
* **Pre-download statistics** — total file count and estimated size are printed before the run starts.
* **Quiet by default** — logs only appear when verbose mode is enabled; no process-global logging side-effects.
* **Update mode** — `--update` skips files that already exist.
* **Path-traversal safe** — hostile `..` segments in API paths are rejected via `safe_join`.
* **RFC 6266 / 5987 filenames** — server-supplied filenames are decoded correctly and sanitized.
* **Configurable TLS** — point at a custom CA bundle via `YDISKARC_TLS_VERIFY` for corporate proxies.

## Installation

### Any OS

A universal installation method (that works on Windows, macOS, Linux, …) is `pip`:

```bash
# Make sure we have an up-to-date version of pip and setuptools:
$ pip install --upgrade pip setuptools

$ pip install --upgrade ydiskarc
```

If `pip` installation fails for some reason, `easy_install ydiskarc` is a fallback.

### Python version

Python version 3.9 or greater is required. The project is tested against 3.9, 3.10, 3.11, and 3.12 on Linux, macOS, and Windows in CI.

## Usage

Synopsis:

```bash
$ ydiskarc [command] [URL] [flags]
```

Examples:

```bash
# Sync command — URL is a positional argument
$ ydiskarc sync https://disk.yandex.ru/d/ABC123 -o output

# Full command — URL is a positional argument
$ ydiskarc full https://disk.yandex.ru/i/XYZ789 -o output

# Parallel sync — download up to 8 files concurrently
$ ydiskarc sync https://disk.yandex.ru/d/ABC123 -o output --parallel 8
```

See also `python -m ydiskarc` and `ydiskarc [command] --help` for help on each command.

## Commands

### `sync`

Synchronizes files and metadata from a public directory resource to a local directory.
Maintains the directory structure and saves metadata for each directory level.

**Basic usage:**

```bash
$ ydiskarc sync https://disk.yandex.ru/d/VVNMYpZtWtST9Q -o mos9maystyle
```

**Update mode** (only download files that don't already exist locally):

```bash
$ ydiskarc sync https://disk.yandex.ru/d/VVNMYpZtWtST9Q -o mos9maystyle --update
```

**Metadata only** (no file downloads):

```bash
$ ydiskarc sync https://disk.yandex.ru/d/VVNMYpZtWtST9Q -o mos9maystyle --nofiles
```

**Parallel downloads:**

```bash
$ ydiskarc sync https://disk.yandex.ru/d/VVNMYpZtWtST9Q -o mos9maystyle --parallel 8
```

**Options:**

- `URL` — public resource URL (required, positional argument).
- `--output`, `-o` — output directory (defaults to the resource ID).
- `--update` — only download files that don't exist locally.
- `--nofiles`, `-n` — metadata-only mode; save metadata without downloading files.
- `--parallel`, `-p` `N` — number of concurrent file downloads (default `1`, sequential).
- `--verbose`, `-v` — enable verbose logging (logs are hidden by default).

The command displays total file count and estimated size before starting downloads.

### `full`

Downloads a single file or a directory. Single files are downloaded with their original format.
Directories are downloaded as ZIP files containing all files inside. For single-file resources, the tool short-circuits the second API call when the metadata response already contains the direct `file` URL.

**Basic usage:**

```bash
$ ydiskarc full https://disk.yandex.ru/i/t_pNaarK8UJ-bQ -o files
```

**With metadata:**

```bash
$ ydiskarc full https://disk.yandex.ru/i/t_pNaarK8UJ-bQ -o files -m
```

**Verbose output:**

```bash
$ ydiskarc full https://disk.yandex.ru/i/t_pNaarK8UJ-bQ -o files -v -m
```

**Options:**

- `URL` — public resource URL (required, positional argument).
- `--output`, `-o` — output directory.
- `--filename`, `-f` — output filename (defaults to `dump.zip`).
- `--metadata`, `-m` — extract and save metadata as `_metadata.json`.
- `--verbose`, `-v` — enable verbose logging.

Notes:

- Single files are downloaded with their original format.
- Directories are downloaded as ZIP files (default filename: `dump.zip`).
- The command displays file count and size information before downloading.

### `configure`

Persists a Yandex OAuth key to `.ydiskarc` with restricted file permissions.

```bash
$ ydiskarc configure --key YOUR_OAUTH_KEY
```

The resulting `.ydiskarc` file is created with mode `0o600` on POSIX systems so the OAuth token is not world-readable. Existing fields in the file are preserved.

**Options:**

- `--key`, `-k` `KEY` — the OAuth token to persist (required).
- `--projectdir`, `-p` `DIR` — directory in which to write `.ydiskarc` (defaults to the current directory).
- `--verbose`, `-v` — enable verbose logging.

Add `.ydiskarc` to your `.gitignore` — the file contains a secret.

### `version`

Prints the installed version:

```bash
$ ydiskarc version
```

## Configuration

### Environment variables

| Variable | Effect |
|----------|--------|
| `YDISKARC_TLS_VERIFY` | Path to a custom CA bundle for TLS verification, `1`/`0` to enable/disable verification. See [TLS verification](#tls-verification). |

### TLS verification

By default `ydiskarc` verifies TLS using the system trust store. Behind a corporate proxy with a private CA, point at the CA bundle:

```bash
$ export YDISKARC_TLS_VERIFY=/etc/pki/corporate-ca.pem
$ ydiskarc sync https://disk.yandex.ru/d/X -o out
```

To disable verification (not recommended):

```bash
$ export YDISKARC_TLS_VERIFY=0
```

### OAuth storage

`.ydiskarc` is a YAML file. The `ydiskarc configure` command writes one with POSIX `0o600` permissions:

```yaml
keys:
  yandex_oauth: your_oauth_key_here
```

The token is currently reserved for future use (the public API endpoints used by `ydiskarc` do not require authentication).

## Architecture

`ydiskarc` follows a modular structure so each concern is in one place:

```
ydiskarc/
├── __init__.py            package metadata (__version__, __all__)
├── __main__.py            `python -m ydiskarc` entry point
├── client.py              YandexDiskClient: HTTP session, retry, rate-limit, URL validation
├── downloader.py          ResourceDownloader: streaming, .part, resume, RFC 5987 filenames
├── models.py              Dataclasses for the Yandex.Disk API JSON shape
├── config.py              Config dataclass: API URLs, timeouts, retries, pool size, TLS verify
├── constants.py           Named constants (HTTP status codes, JSON keys, filenames)
├── core.py                Typer commands (thin wrappers around Project)
└── cmds/
    ├── __init__.py        re-exports Project
    └── processor.py       Project facade + recursive walker (safe_join, PathTraversalError)
```

The `Project` class is the single public entry point for the recursive walker logic. Recursive functions live as private helpers (`_yd_get_full`, `_yd_get_and_store_dir`, `_scan_directory_for_stats`); they cannot be imported directly. The Typer commands in `core.py` instantiate `Project` and delegate.

See [`openspec/specs/core-architecture/spec.md`](openspec/specs/core-architecture/spec.md) for the authoritative behaviour specification.

## Troubleshooting

### Common Issues

**"No download url. Probably wrong public url/key?"**

- Verify the URL is correct and the resource is publicly accessible.
- Check that the URL format matches: `https://disk.yandex.ru/d/...` or `https://disk.yandex.ru/i/...`.

**"Failed to download file" or network errors**

- Check your internet connection.
- The tool automatically retries on transient failures.
- For rate limiting, the tool will wait and retry automatically based on `Retry-After`.

**"Failed to create directory"**

- Check file system permissions.
- Ensure you have write access to the output directory.

**Resume interrupted downloads**

- Downloads automatically resume if interrupted.
- Partial files are detected and resumed from the last byte (HTTP `Range:` request).

### Verbose Mode

By default, `ydiskarc` runs quietly and only shows progress bars and essential information. For detailed debugging information, use the `--verbose` / `-v` flag:

```bash
$ ydiskarc sync https://disk.yandex.ru/d/... -o output -v
```

When verbose mode is enabled:

- Detailed logging of all operations (on the `ydiskarc` package logger; other libraries' logs are not muted).
- File-by-file download progress.
- API request details.
- Error stack traces.

## Examples

**Download a public folder:**

```bash
$ ydiskarc sync https://disk.yandex.ru/d/ABC123 -o my_backup
```

**Parallel sync of a large folder:**

```bash
$ ydiskarc sync https://disk.yandex.ru/d/ABC123 -o my_backup --parallel 8
```

**Download a single file with metadata:**

```bash
$ ydiskarc full https://disk.yandex.ru/i/XYZ789 -o downloads -m
```

**Update existing backup (skip existing files):**

```bash
$ ydiskarc sync https://disk.yandex.ru/d/ABC123 -o my_backup --update
```

**Get metadata only:**

```bash
$ ydiskarc sync https://disk.yandex.ru/d/ABC123 -o metadata_only --nofiles
```

**Example output:**

```
Total files to download: 7
Total size: 10.12 MB
Downloading file1.pdf: 100%|████████████| 1.72M/1.72M [00:05<00:00, 345KB/s]
Downloading file2.pdf: 100%|████████████| 980K/980K [00:03<00:00, 290KB/s]
...
```

## Security & dependency updates

The repository uses [Dependabot](https://github.com/ruarxive/ydiskarc/network/dependencies) to open weekly pull requests for outdated pip and GitHub Actions dependencies. A `pip-audit` Software Composition Analysis (SCA) job runs on every CI build to detect known vulnerabilities in the dependency tree. PRs that introduce vulnerable dependencies fail the build.

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **OpenSpec first.** Non-trivial changes (new features, breaking changes, architecture shifts) MUST start as an OpenSpec proposal under `openspec/changes/<id>/`. See [openspec/AGENTS.md](openspec/AGENTS.md) for the workflow.
2. **Fork** the repository and create a feature branch.
3. **Write tests** for every new public helper or command.
4. **Follow code style** — the project uses:
   - `black` for formatting (line length: 100)
   - `flake8` and `ruff` for linting
   - `isort` (`--profile black`) for import ordering
   - `mypy` for type hints (best-effort, `--ignore-missing-imports`)
5. **Run the full check suite** before submitting:

   ```bash
   pip install -r requirements-dev.txt
   pytest --cov=ydiskarc --cov-fail-under=70
   black --check --line-length=100 ydiskarc tests
   isort --check-only --profile black --line-length 100 ydiskarc tests
   flake8 ydiskarc tests --max-line-length=100 --extend-ignore=E203,W503
   ```

6. **Install pre-commit hooks** (recommended):

   ```bash
   pip install pre-commit
   pre-commit install
   ```

7. **Submit a pull request** with a clear description and a link to the OpenSpec change.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/ruarxive/ydiskarc.git
cd ydiskarc

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests with coverage
pytest --cov=ydiskarc --cov-report=term-missing

# Run linting
flake8 ydiskarc tests --max-line-length=100 --extend-ignore=E203,W503
ruff check ydiskarc tests
black --check --line-length=100 ydiskarc tests
isort --check-only --profile black --line-length 100 ydiskarc tests

# Run mypy (best-effort)
mypy ydiskarc --ignore-missing-imports
```

### Releasing

Releases are published to PyPI automatically when a maintainer pushes a tag matching `v*.*.*` (e.g. `v1.2.0`). The `release` workflow uses OIDC trusted publishing — no long-lived PyPI token is needed.

Manual release steps for maintainers:

1. Bump `__version__` in `ydiskarc/__init__.py`.
2. Add a release entry to `CHANGELOG.md` under a new `[X.Y.Z]` heading, moving the `[Unreleased]` items into it.
3. Commit and push: `git commit -am "Release vX.Y.Z"` then `git tag vX.Y.Z && git push --tags`.
4. Watch the `Release` workflow on GitHub Actions.

## Metadata Documentation

For detailed information about the Yandex.Disk API metadata structure:

- [Examples Directory](examples/) — contains example metadata file and documentation.
- [Metadata Structure Documentation](examples/METADATA_STRUCTURE.md) — complete reference of metadata fields.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed list of changes.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Links

- **Repository**: https://github.com/ruarxive/ydiskarc/
- **Issues**: https://github.com/ruarxive/ydiskarc/issues
- **Changelog**: https://github.com/ruarxive/ydiskarc/blob/main/CHANGELOG.md
- **Yandex.Disk API**: https://yandex.com/dev/disk/api/