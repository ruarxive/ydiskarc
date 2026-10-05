# Repository Analysis and Improvement Suggestions

**Last Updated:** 2026-10-05 (Comprehensive Code Review — Post-Refactor Audit)

## Executive Summary

`ydiskarc` is a small (~520 LOC), well-structured Python 3.9+ CLI for backing up public Yandex.Disk resources, built on Typer, `requests`, and `tqdm`. The codebase was recently refactored (see `openspec/changes/archive/2026-03-08-refactor-architecture/`) from a monolithic `processor.py` into focused modules (`client.py`, `downloader.py`, `models.py`, `config.py`), and it shows: responsibilities are clear, tests pass cleanly (20/20), pre-commit and CI are in place, and modern practices are followed.

This audit confirms the refactor landed well and identifies **remaining issues** that did not exist in the prior analysis or that survived it. Categorized counts: **3 high-priority bugs**, **6 medium-priority quality/security gaps**, **5 low-priority refactors**, and **7 enhancement ideas**.

### Headline Findings

| # | Severity | Finding |
|---|----------|---------|
| 1 | 🔴 High | `setup_logging(verbose=False)` calls `logging.disable(CRITICAL)`, a process-global sticky switch — once set, no later logger can output, including within the same CLI run for any module-level warning |
| 2 | 🔴 High | `setup_logging(verbose=True)` uses `logging.basicConfig(...)`, which is a **no-op** once any other code (even transitively) has configured logging — verbose mode is silently broken on real-world installations |
| 3 | 🔴 High | **Path-traversal risk** in `yd_get_and_store_dir` / `scan_directory_for_stats` — API-supplied `path` values are joined into `os.path.join(output, *parts)` without normalization or `..` check, allowing writes outside the output directory if the upstream API returns hostile names |
| 4 | 🟡 Med | Rate-limit-retry block is duplicated three times across `client.py` and `downloader.py` |
| 5 | 🟡 Med | No `__all__` in any package — public API surface is undocumented |
| 6 | 🟡 Med | `mypy || true` in `.github/workflows/ci.yml:84` — typing regressions do not fail CI |
| 7 | 🟡 Med | `tox.ini` pins `py38` (EOL) and `.pre-commit-config.yaml` says `--python-version=3.6`, both contradicting `pyproject.toml`'s `>=3.9` |
| 8 | 🟡 Med | `Project.configure()` (writes OAuth key to `.ydiskarc`) is **not exposed via any CLI command** — dead code, also stores OAuth plaintext with no `chmod 600` |
| 9 | 🟡 Med | Tests do not exercise the resume path, the `aria2` branch, rate-limit retry, or `yandex.com` URLs (only `.ru` is tested) |

---

## 1. Architecture Overview

```
ydiskarc/
├── __init__.py            (164 B)   — package metadata only
├── __main__.py            (956 B)   — `python -m ydiskarc` entry, error-translation shim
├── client.py              (3 350 B)  — `YandexDiskClient`: session, retries, rate limit, URL validation, GET /download
├── downloader.py         (7 217 B)  — `ResourceDownloader`: streaming, .part, resume, aria2 fallback
├── models.py             (3 004 B)  — Dataclasses for the Yandex API JSON shape
├── config.py             (1 215 B)  — `Config` dataclass: API URLs, chunk size, timeout, retries, UA
├── core.py               (4 556 B)  — Typer app + three commands (`sync`, `full`, `version`)
└── cmds/
    ├── __init__.py        (empty)
    └── processor.py      (7 200 B)  — `Project` facade + module-level orchestration helpers
```

**Strengths.**
- Module responsibilities are clean: `client` owns HTTP, `downloader` owns file I/O, `models` owns JSON shape, `config` owns constants, `cmds/processor` orchestrates.
- The `Project` class is a thin facade delegating to module-level helpers (`yd_get_full`, `yd_get_and_store_dir`, `scan_directory_for_stats`) — easy to test and easy to read.
- `_metadata.json` per-directory is a useful design for archival workflows (preserves provenance).

**Weaknesses.**
- The directory iteration in `yd_get_and_store_dir` is **recursive** (default for any non-empty `path`) — see *Performance* below.
- `processor.py` mixes three concerns — CLI orchestration (`Project.sync`/`full`), directory scanning (`scan_directory_for_stats`), and the recursive download loop (`yd_get_and_store_dir`). The refactor goal was single-responsibility modules; the file still does three jobs.
- Module-level helpers (`yd_get_full`, `yd_get_and_store_dir`, `scan_directory_for_stats`) bypass `Project` entirely — `Project.full` is just `yd_get_full(...)`, `Project.sync` is `self.__store(...)`. The facade is a thin pass-through; either delete it or make it the single entry point.
- `cmds/__init__.py` is empty — there's no public re-export, so callers cannot `from ydiskarc.cmds import Project`.

---

## 2. Bug Findings (with Reproduction)

### 🔴 Bug 1 — `logging.disable(CRITICAL)` is process-wide and irreversible from `setup_logging`

**File:** `ydiskarc/core.py:21–34`

```python
def setup_logging(verbose: bool = False) -> None:
    if verbose:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
        )
    else:
        # Disable logging when not verbose
        logging.disable(logging.CRITICAL)
```

**Why it matters.** `logging.disable()` is a process-global *override* that disables every logger at or below the given level regardless of any handler or level configuration. It is **sticky** until the process exits. Two consequences:

1. Any third-party library (e.g., `urllib3`, `requests`) that emits a `WARNING` from import time will be muted for the rest of the run — even when the user later asks for verbose output via a different code path.
2. If a future feature calls `setup_logging(verbose=False)` first and then `setup_logging(verbose=True)` (e.g., in a daemon mode), the disable persists and the verbose branch's `basicConfig` is silently ineffective.

**Fix.** Configure a `ydiskarc`-namespaced logger with a `NullHandler` and only attach a `StreamHandler` when `verbose=True`. Do **not** call `logging.disable()`.

```python
import logging

PKG_LOGGER = "ydiskarc"

def setup_logging(verbose: bool = False) -> None:
    logger = logging.getLogger(PKG_LOGGER)
    logger.setLevel(logging.DEBUG if verbose else logging.WARNING)
    # Drop any handlers we previously attached to avoid duplication
    for h in list(logger.handlers):
        logger.removeHandler(h)
    if verbose:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(h)
    # If a parent is not configured (typical CLI), ensure propagation carries messages
    if not logger.parent.handlers and not logger.handlers:
        logger.addHandler(logging.NullHandler())
```

### 🔴 Bug 2 — `logging.basicConfig(...)` in verbose mode is a no-op on real installations

**File:** `ydiskarc/core.py:27–30`

`basicConfig` only configures logging when the root logger has no handlers. As soon as **anything** in the import graph (a pytest plugin, a debugger, an IDE shim, or even a `tqdm` import that already configures handlers) has touched logging, this call silently does nothing. Verified empirically:

```
>>> logging.basicConfig(level=logging.CRITICAL, format='X')
>>> logging.basicConfig(level=logging.DEBUG)         # second call
>>> logging.getLogger().getEffectiveLevel() == logging.DEBUG
False
```

**Fix.** Replace with the namespaced-logger approach in Bug 1's snippet (uses `setLevel` on a child logger, which is reliable).

### 🔴 Bug 3 — Path traversal through API-controlled `path`

**File:** `ydiskarc/cmds/processor.py:107–111, 137–139, 154–156, 170–173`

```python
arr = [output] + [i.rstrip() for i in row["path"].split("/") if i.strip()]
file_path = os.path.join(*arr[:-1])
file_name = arr[-1]
full_file_path = os.path.join(file_path, file_name)
```

The `row["path"]` and `path` arguments come from the Yandex.Disk API and are joined into the output path with no normalization. A hostile or buggy API response containing `..` or absolute segments would write outside `output`. Even *benign* names with leading whitespace + `..` (`"  /etc/passwd"`) slip through `rstrip()` (which only strips trailing whitespace).

**Fix.** Centralize path construction in a single helper:

```python
def safe_join(base: str, *parts: str) -> str:
    """Join path components and ensure the result stays under base."""
    base_abs = os.path.realpath(base)
    candidate = os.path.realpath(os.path.join(base_abs, *(p.strip() for p in parts if p.strip())))
    if os.path.commonpath([base_abs, candidate]) != base_abs:
        raise ValueError(f"Path traversal detected: {candidate!r} escapes {base_abs!r}")
    return candidate
```

Use `safe_join(output, *row["path"].split("/"))` everywhere instead of inline `os.path.join(*arr)`.

**Test coverage:** add `tests/test_processor.py::test_path_traversal_blocked` that feeds an API response with `"path": "../../etc/passwd"` and asserts `ValueError`.

---

## 3. Code Quality Issues

### 🟡 3.1 Rate-limit retry block is duplicated three times

**Files:**
- `ydiskarc/client.py:67–72` (`get_resource_metadata`)
- `ydiskarc/client.py:77–84` (`get_download_link`)
- `ydiskarc/downloader.py:51–68` and `113–131` (initial + resume GET in `get_file`)

The pattern is identical:
```python
resp = session.get(url, ...)
if resp.status_code == 429:
    self.client.handle_rate_limit(resp)
    resp = session.get(url, ...)
resp.raise_for_status()
```

**Fix.** Add a thin wrapper on `YandexDiskClient`:

```python
def _request_with_backoff(self, method: str, url: str, **kwargs) -> requests.Response:
    resp = self.session.request(method, url, **kwargs)
    if resp.status_code == 429:
        self.handle_rate_limit(resp)
        resp = self.session.request(method, url, **kwargs)
    resp.raise_for_status()
    return resp
```

`downloader.py` can either accept the client and call it (cleaner) or keep using the raw session but call a free function. The point is to delete the duplication.

### 🟡 3.2 `verify=True` is hardcoded — testing/proxy workflows have no override

`downloader.py:55, 65, 118, 128` all pass `verify=True` directly. Combined with `requests.Session` not exposing `verify` from `Config`, this is fine for production but blocks two legitimate cases:

- **Self-hosted proxies with custom CA bundles** — user has no way to set `REQUESTS_CA_BUNDLE`.
- **Corporate mitmfs** — users must edit code rather than set `verify` via env or flag.

**Fix.** Add `verify: Optional[str | bool] = True` to `Config`, pass through to the adapter, document `YDISKARC_TLS_VERIFY` env override.

### 🟡 3.3 `id` shadows the Python builtin

`ydiskarc/cmds/processor.py:35`
```python
id = url.rsplit("/", 1)[-1]
```
The builtin `id()` returns the memory address of an object — harmless here, but a linter should flag this (and one day will, when flake8/ruff enable the rule).

**Fix.** Rename to `resource_id` or `_id`.

### 🟡 3.5 `core.py:119` URL parsing strips the resource identifier correctly but is duplicated logic with `cmds/processor.py:35`

Two separate places compute the resource ID from a URL with two slightly different idioms:
```python
# core.py:119
output = url.rsplit("/d/", 1)[-1] if "/d/" in url else url.rsplit("/i/", 1)[-1]
# processor.py:35
id = url.rsplit("/", 1)[-1]
```
The `core.py` version handles both `/d/` and `/i/` prefixes (good); the `processor.py` version naively takes the last segment (works for current shapes but breaks if Yandex ever changes URL layouts, and ignores query strings — a malformed URL with `?ref=...` would corrupt the directory name). Centralize in `client.py` next to `validate_yandex_url`.

### 🟡 3.6 Magic strings / numbers scattered

- `'_metadata.json'` (processor.py:24, 141)
- `'dump.zip'` (processor.py:40)
- `'_embedded'`, `'items'`, `'path'`, `'type'`, `'size'`, `'file'` (processor.py repeatedly)
- Status codes `429`, `503`, etc.

Move to `ydiskarc/constants.py`:
```python
METADATA_FILENAME = "_metadata.json"
DEFAULT_FULL_FILENAME = "dump.zip"
RATE_LIMITED = 429
API_LIST_LIMIT = 1000
```

---

## 4. Security Findings

### 🟡 4.1 Plaintext OAuth storage with no file permission hardening

`Project.configure()` (processor.py:193–209) writes an OAuth token to `<projectdir>/.ydiskarc` using `yaml.safe_dump`. The token is stored in plaintext, with default umask (typically `0o644` world-readable on Linux/macOS). Worse: **the method is not wired to any Typer command in `core.py`** — it is dead code that nonetheless describes an insecure pattern if it ever becomes live.

**Fix.**
1. Either delete `configure()` or wire it as `ydiskarc configure --key ...` and add `os.chmod(filepath, 0o600)` after write.
3. Mention in `README.md` to add `.ydiskarc` to `.gitignore`.

### 🟡 4.2 Content-Disposition filename decoding is naive

`downloader.py:78–84`:
```python
fname = (
    re.findall("filename=(.+)", page.headers["Content-Disposition"])[0]
    .strip('"')
    .encode("latin-1")
    .decode("utf-8")
)
```
This will:
- Treat `filename*=` (RFC 5987) as not present
- Match `filename=...; filename=...` ambiguously
- Crash on filenames containing literal newlines or CRLF injection

**Fix.** Use `requests`' built-in helper or `email.message.Message` parsing; otherwise explicitly handle `filename*=UTF-8''...` first.

### 🟡 4.3 `aria2` path is taken verbatim and passed to `subprocess.run`

`downloader.py:184–195`. `aria2path` is the *first positional* arg passed by the user. While the CLI doesn't currently surface it, the parameter is part of the public API and a caller could pass arbitrary binaries. Not exploitable as long as it's not wired to a CLI option, but worth noting.

### 🟢 4.4 `verify=True` hardcoded
See §3.2.

### 🟢 4.5 No Dependabot / no SCA scanning in CI

`requirements.txt` pins no upper bounds. `PyYAML>=6.0.1` is fine today; a future CVE in `requests` (cf. CVE-2024-35195 in `requests`/`urllib3` SESSION verify) would slip through. Add `github/dependabot.yml` and either `bandit` or `pip-audit` to CI.

---

## 5. Testing Gaps

20 tests pass; coverage is reasonable for happy paths but the following are uncovered or under-covered.

| Path | Where | Risk |
|---|---|---|
| `ResourceDownloader.get_file` resume branch | `downloader.py:107–136` | No test exercises `os.path.exists(part_filename) is True` path |
| `aria2` branch | `downloader.py:183–200` | Untested; parameter is also unreachable from CLI |
| 429 retry in `client.get_resource_metadata` / `get_download_link` | `client.py:67–72, 80–84` | Mocked client always returns 200 |
| `validate_yandex_url` for `.com` TLDs | `client.py:47–56` | Only `.ru` patterns tested |
| Path traversal | `processor.py:107–111, 137–139` | Not blocked, not tested (see Bug 3) |
| `setup_logging(verbose=True)` actually produces output | `core.py:27–30` | Confirmed broken by hand; no test catches it |
| `aria2path` validation | `downloader.py:184` | No test that `ValueError` is raised |
| `Project.configure()` | `processor.py:193–209` | Dead code, untested path |

**Recommended test additions** (ordered by value):
1. `test_path_traversal_blocked` — high-value security test
2. `test_verbose_logging_emits` — would catch Bug 2
3. `test_resume_from_part_file` — would catch a regression in the `.part` invariant
5. `test_rate_limit_retry` — exercises `handle_rate_limit` mocked path
6. `test_aria2_missing_path` — defensive test
7. `test_validate_yandex_url_dotcom` — covers the four-pattern regex

**Coverage tooling.** Add `pytest-cov` to `requirements-dev.txt`, run with `--cov=ydiskarc --cov-fail-under=85` in CI.

---

## 6. CI/CD and DevOps

### 🟡 6.1 `mypy || true` masks typing regressions

`.github/workflows/ci.yml:84`:
```yaml
- name: Type check
  run: mypy ydiskarc --ignore-missing-imports || true
```
A `mypy` regression cannot fail the build. Either remove `|| true` or split into a dedicated `lint` job that fails fast.

### 🟡 6.2 Tox targets EOL Python 3.8

`tox.ini:7`:
```
envlist = py38
```
`pyproject.toml` requires `>=3.9`. The CI matrix is `3.9/3.10/3.11` — tox is the odd one out. Update to `envlist = py39,py310,py311,py312`.

### 🟡 6.3 Pre-commit pins Python 3.6

`.pre-commit-config.yaml:38`:
```yaml
args: ['--ignore-missing-imports', '--python-version=3.6']
```
This will silently skip checks that don't exist in 3.6 (e.g., PEP 604 unions in 3.10+). Use `3.9` to match `pyproject.toml`.

### 🟡 6.4 No `mypy` invocation in the `lint` job, no `isort`/`ruff`

The `lint` job runs `flake8`, `black --check`, `mypy` — but no `isort` or `ruff`, even though `.pre-commit-config.yaml` defines `isort` and the README documents `ruff` as a quality gate. Add them; `ruff` is fast enough to run unconditionally.

### 🟢 6.5 No release automation

No `release.yml`; tags and PyPI uploads are manual. Add a GitHub Actions workflow that builds and publishes on tag push (using `pypa/gh-action-pypi-publish` with OIDC trusted publishing).

### 🟢 6.6 Coverage not tracked

No `codecov.yml`, no `--cov` in CI. Add `pytest-cov` and Codecov (or `coverage-badge`).

### 🟢 6.7 Action versions are dated

`actions/checkout@v3`, `actions/setup-python@v4`, `actions/cache@v3` — bump to `v4`/`v5` to pick up Node 20 runtime and security fixes.

---

## 7. Performance

### 🟡 7.1 Recursive `yd_get_and_store_dir` — single connection per file

`processor.py:122–184` recurses synchronously into every subdirectory, calling the API once per directory and downloading one file at a time. For a 1k-file resource on a healthy link, the wall time is dominated by request round-trips.

**Options (in order of complexity):**
1. **Page through `_embedded.items`** using `limit`/`offset`. Currently `limit=1000` is passed; if the directory has more, `items` will be paginated and the rest is silently dropped. Use `offset` to follow.
2. **ThreadPoolExecutor for downloads** — add a `--parallel N` option. The API supports this since requests are independent.
3. **Persistent session per worker** — already done by `client.session`; just make it thread-safe (one session shared with `HTTPAdapter(pool_connections=N, pool_maxsize=N)`).

### 🟡 7.2 `verify=True` on every request — fine, but no `pool_maxsize`

`HTTPAdapter(max_retries=...)` doesn't set `pool_connections`/`pool_maxsize`, so the default (10) is used. For parallel downloads, raise this to match `--parallel N`.

### 🟢 7.3 `chunk_size = 32 * 1024` is conservative

32 KB is a safe lower bound for flaky networks but adds syscall overhead on fast links. For typical Yandex public resources (CDN-fronted), 256 KB–1 MB is more appropriate. Make it configurable in `Config` or via env var.

### 🟢 7.4 Two API round-trips per file (metadata + download link)

`full` command does `get_resource_metadata` then `get_download_link` for the URL. For directories, every directory visit is two HTTP calls (one for the listing, one per file via the `file` field in the listing — actually only one call per file because `file` is in the listing). So `full` for files wastes one call vs. `sync`. Could fetch the download link directly from the listing's `file` field for known single-file URLs.

---

## 8. Documentation

### 🟢 8.1 CHANGELOG has duplicate `[1.1.0]` and `[Unreleased]` entries

`CHANGELOG.md:13–60` lists the same changes under both `[1.1.0]` and `[Unreleased]`. Consolidate into a single `[Unreleased]` block, or move unreleased changes into a `[1.2.0]` placeholder.

### 🟢 8.2 README says Python 3.6+, pyproject.toml says 3.9+

`README.md:38` says "Python version 3.6 or greater is required" but `pyproject.toml:10` says `>=3.9`. The README is stale.

### 🟢 8.3 OpenSpec `project.md` is a placeholder

`openspec/project.md` contains only template fill-in markers (`[Describe your project's purpose...]`). Populate it (purpose, tech stack, conventions, testing strategy, git workflow) per `openspec/AGENTS.md:44`.

### 🟢 8.4 Spec for the refactor is missing `## Purpose`

`openspec/specs/core-architecture/spec.md:4`:
```
## Purpose
TBD - created by archiving change refactor-architecture. Update Purpose after archive.
```
The TODO is from the archive step — needs filling in.

### 🟢 8.5 OpenSpec `AGENTS.md` duplicates the project's `AGENTS.md` content

`openspec/AGENTS.md` is the upstream OpenSpec instructions; it doesn't reference the project's own `AGENTS.md` (which describes the ydiskarc architecture). Link the two or note the relationship.

---

## 9. Suggested Action Plan

### Phase 1 — Bug fixes (this week)
1. Replace `setup_logging` with namespaced-logger approach (§Bug 1, §Bug 2).
2. Add `safe_join` helper and route all path constructions through it; add traversal test (§Bug 3).
3. Remove `id =` builtin shadow (§3.3).
4. Add the missing test cases from §5 (#1–#5).

### Phase 2 — Quality + security (this sprint)
1. `_request_with_backoff` to dedupe rate-limit logic (§3.1).
2. `Config.verify` + env override (§3.2, §4.4).
3. Move magic strings to `constants.py` (§3.6).
4. `Content-Disposition` parsing hardening via RFC 5987 path (§4.2).
5. `Project.configure()` — either delete or wire + `chmod 600` (§4.1).
6. CI: remove `mypy || true`; bump `actions/*` to v4/v5; bump tox envlist; bump pre-commit python to 3.9 (§6.1–6.3, §6.7).
7. README Python-version correction; CHANGELOG consolidation; OpenSpec `project.md` and `spec.md Purpose` (§8.1–8.4).

### Phase 3 — Performance + features (next sprint)
1. `--parallel N` for sync (§7.1).
2. `pool_maxsize` from `Config` (§7.2).
3. `chunk_size` from `Config` (§7.3).
4. Skip duplicate API call in `full` when `file` URL is in metadata (§7.4).
5. Add `pytest-cov` and Codecov badge (§6.6).
6. Add Dependabot + `pip-audit` (§4.5).
7. Add release workflow (§6.5).

### Phase 4 — Code organization (later)
1. Collapse `Project` facade or remove it; let `core.py` call `yd_get_full` / `yd_get_and_store_dir` directly (§1).
2. Move recursive iteration in `yd_get_and_store_dir` to a `DirectoryWalker` class so `sync` and `full-dir` can share.
3. Add `__all__` to each module (§headline #5).

---

## 10. Strengths Worth Preserving

The refactor moved the codebase from a single 800-LOC `processor.py` to four focused modules. The result is genuinely better:

- **`Config` dataclass** with derived URLs and auto-User-Agent is a clean pattern.
- **`ResourceDownloader` as an injected dependency** of `YandexDiskClient.session` keeps HTTP details in `client.py` and file-I/O details in `downloader.py`.
- **`models.py` dataclasses** with `from_dict` constructors make it easy to swap to `pydantic` later without rippling through the code.
- **`safe_part_filename`** in `downloader.py` — the `.part` invariant is the single most important safety property of this tool and it is implemented correctly. Test it (Phase 1 #4).
- **URL validation** at the CLI boundary keeps bad input from reaching the API layer.
- **`logging.disable` was likely the wrong tool**, but the *intent* (quiet by default) is good — namespaced loggers achieve the same UX without breaking downstream.

---

## Quick Wins (≤30 min each)

- ☐ Rename `id = url.rsplit(...)` → `resource_id`
- ☐ Add `__all__ = [...]` to each module
- ☐ Add `pytest-cov` to requirements-dev and CI
- ☐ Remove `mypy || true`
- ☐ Bump `tox.ini` envlist
- ☐ Bump `.pre-commit-config.yaml` Python to 3.9
- ☐ Fix README Python version requirement
- ☐ Fix CHANGELOG duplicate `[Unreleased]` block
- ☐ Fill in `openspec/project.md` and `openspec/specs/core-architecture/spec.md` Purpose
- ☐ Add `tests/test_processor.py::test_path_traversal_blocked` (will fail until §Bug 3 is fixed)

---

## References

- `ydiskarc/core.py:21` — `setup_logging` (Bugs 1 & 2)
- `ydiskarc/cmds/processor.py:107, 137, 154, 170` — path-traversal sinks (Bug 3)
- `ydiskarc/client.py:67, 77` — duplicated rate-limit retry (3.1)
- `ydiskarc/downloader.py:51, 113` — same duplication in streaming path
- `ydiskarc/cmds/processor.py:35` — `id` builtin shadow (3.3)
- `ydiskarc/cmds/processor.py:193` — `Project.configure()` dead code (4.1)
- `.github/workflows/ci.yml:84` — `mypy || true` (6.1)
- `tox.ini:7` — py38 EOL (6.2)
- `.pre-commit-config.yaml:38` — Python 3.6 (6.3)
- `CHANGELOG.md:13–60` — duplicate entries (8.1)
- `README.md:38` — stale Python 3.6+ claim (8.2)
- `openspec/project.md` — placeholder (8.3)
- `openspec/specs/core-architecture/spec.md:4` — TBD Purpose (8.4)