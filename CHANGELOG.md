# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-10-05

### Added
- `ydiskarc constants` module — single source of truth for repeating string/number literals (filenames, HTTP status codes, Yandex API JSON keys).
- `ydiskarc configure --key <KEY>` CLI command — wires the previously-dead `Project.configure()` and writes `.ydiskarc` with POSIX `0o600` permissions.
- `--parallel N` option for `sync` — parallelises file downloads via a thread pool (`ThreadPoolExecutor`). `Config.pool_maxsize` scales the HTTP connection pool to match.
- `YDISKARC_TLS_VERIFY` environment variable — point at a custom CA bundle for corporate proxies, or set to `0` to disable verification.
- `Project` is the single public entry point to the recursive walker; `_yd_get_full`, `_yd_get_and_store_dir`, `_scan_directory_for_stats` are private (cannot be imported directly). Added explicit `__all__` to `ydiskarc/cmds/processor.py`.
- `_yd_get_full` short-circuits the second `get_download_link` API call when the metadata response for a single-file resource already contains a `file` URL — one fewer HTTP round-trip on the hot path.
- `.github/dependabot.yml` — weekly PRs for outdated `pip` and `github-actions` dependencies.
- `.github/workflows/release.yml` — tag-triggered PyPI publish via OIDC trusted publishing; no long-lived API token.
- `pip-audit` SCA job in CI — fails the build on known CVEs in the dependency tree.
- `pytest-cov` enforced in CI with `--cov-fail-under=70`; Codecov upload.
- Documentation of the architecture (`README.md` §Architecture) and the release process (`README.md` §Releasing).

### Changed
- `setup_logging` rewritten to use a namespaced `ydiskarc` package logger; the previous implementation invoked `logging.disable(CRITICAL)` (a process-global side-effect) and `logging.basicConfig` (a silent no-op once any other library has touched logging), making `-v` ineffective in real-world installations.
- `safe_join` helper added to `ydiskarc/cmds/processor.py`; all four inline `os.path.join(*arr)` sites route through it. Path-traversal attempts are now skipped instead of writing outside the output directory.
- Rate-limit retry (originally duplicated three times) consolidated into `YandexDiskClient._request_with_backoff`. `ResourceDownloader._probe` delegates to the same helper.
- All HTTP `Content-Disposition` parsing rewritten to follow RFC 6266 / 5987 (`filename*=UTF-8''...`) and sanitize the result before use as a local filename (`parse_content_disposition`, `sanitize_filename`).
- CI hardened: removed `|| true` from the mypy step; bumped GitHub Actions to v4/v5; added `isort` and `ruff` to the lint job; bumped the Python matrix to 3.9–3.12 on Linux/macOS/Windows.
- `tox.ini` updated from `py38` (EOL) to `py39,py310,py311,py312`.
- Pre-commit mypy hook now targets Python 3.9 (was 3.6).
- README "Python 3.6+" claim corrected to "Python 3.9+".
- Every `ydiskarc` module now declares an explicit `__all__`.

### Fixed
- `logging.basicConfig` no longer masks third-party library warnings (`urllib3`, `requests`).
- Hostile API paths containing `..` segments can no longer write outside the user-chosen output directory.
- Filenames containing CRLF or path separators are sanitized before use.
- The previously-dead `Project.configure()` is now reachable from the CLI.

## [1.1.0] - 2025-12-15

### Changed
- **BREAKING**: Changed URL from option (`--url`) to positional argument for `sync` and `full` commands.
- Replaced Rich progress bars with tqdm for better compatibility and performance.
- Made logging conditional — logs only appear when `--verbose` flag is used.
- Changed default output filename for `full` command to `dump.zip` instead of auto-detected name.

### Added
- **Progress bars with tqdm** — visual progress indicators for file downloads.
- **Pre-download statistics** — shows total file count and estimated size before downloading.
- **Examples directory** — added example metadata file and comprehensive documentation.
- **Metadata structure documentation** — detailed documentation of Yandex.Disk API metadata format.

### Fixed
- All linting issues (flake8, ruff, black, isort).
- Type annotation issues.
- Code formatting and style consistency.

## [1.0.1] - 2021-11-26

### Added
- First public release on PyPI and updated GitHub code.