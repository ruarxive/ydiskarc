# Project Context

## Purpose

`ydiskarc` (pronounced *Ai-disk-arc*) is a command-line tool that backs up public
resources (files and directories) from Yandex.Disk. The tool exists because
Yandex.Disk provides a free-to-use public API for shared resources, and an
archival workflow needs a way to mirror a snapshot of any shareable folder onto a
local filesystem with metadata preserved.

## Tech Stack

- **Language**: Python 3.9+
- **CLI framework**: [Typer](https://typer.tiangolo.com/) (built on Click)
- **HTTP client**: [requests](https://requests.readthedocs.io/) with
  `urllib3.util.retry.Retry` for transport-level retries
- **Progress bars**: [tqdm](https://tqdm.github.io/)
- **YAML config**: [PyYAML](https://pyyaml.org/) (`safe_load` / `safe_dump`)
- **Packaging**: PEP 517 / 518 `pyproject.toml` (setuptools build backend)

## Project Conventions

### Code Style
- Black formatting, line length 100.
- Flake8 linting with `--max-line-length=100 --extend-ignore=E203,W503`.
- isort with `--profile black`.
- Ruff for fast lint.
- Mypy (best-effort, `--ignore-missing-imports`).
- All public modules MUST declare `__all__` listing their public symbols.
- All repeating literals MUST live in `ydiskarc/constants.py`.

### Architecture Patterns
- Module responsibilities are single-purpose:
  - `client.py` — HTTP session, retry, rate-limit handling, URL validation.
  - `downloader.py` — file I/O, `.part` invariants, resume, optional `aria2` backend.
  - `models.py` — dataclasses for the Yandex API JSON shape.
  - `config.py` — runtime tunables (timeouts, chunk size, retry count).
  - `constants.py` — names for repeating literals.
  - `cmds/processor.py` — orchestration of the recursive walk.
  - `core.py` — Typer commands (thin wrappers around `cmds/processor.py`).
- `Project` is a thin facade. Each command routes to a module-level helper
  (`yd_get_full`, `yd_get_and_store_dir`, `scan_directory_for_stats`).
- Logging uses a namespaced `ydiskarc` logger; never mutates the root logger
  with `basicConfig` or `disable`.

### Testing Strategy
- `pytest` with `unittest.mock` for unit tests.
- All new behavior MUST have a unit test.
- CI runs flake8 + black + isort + ruff + pytest for Python 3.9–3.12 on
  Linux, macOS, and Windows.
- A change MUST NOT break an existing test.

### Git Workflow
- `main` is the default branch; PRs target `main`.
- Each non-trivial change is preceded by an OpenSpec proposal under
  `openspec/changes/<kebab-id>/`.
- After deployment, proposals are archived to
  `openspec/changes/archive/YYYY-MM-DD-<id>/` and their spec deltas folded
  into `openspec/specs/`.

## Domain Context

- Yandex.Disk public API: `https://cloud-api.yandex.net/v1/disk/public/resources`
  (metadata) and `.../public/resources/download` (download link).
- The Yandex API limits listing to 1,000 items per request; directories larger
  than that need pagination via `offset`.
- The `file` field in the listing contains a time-limited direct download URL.
- URLs use the form `https://disk.yandex.ru/d/<id>` (directory) or
  `https://disk.yandex.ru/i/<id>` (single file); `.com` is also accepted.

## Important Constraints

- **Public resources only.** The tool does not and cannot authenticate against
  private Yandex accounts in the current implementation; OAuth storage
  (`Project.configure`) is reserved for future use.
- **Forward compatibility.** No breaking CLI changes without a `[Unreleased]`
  BREAKING entry in `CHANGELOG.md`.
- **POSIX file permissions.** Configuration files holding OAuth keys MUST be
  created with `0o600` mode on POSIX; on Windows the chmod call is a
  best-effort no-op.

## External Dependencies

- Yandex.Disk Public API (no SLA; rate-limited).
- Python 3.9+ runtime.
- POSIX or Windows filesystem.