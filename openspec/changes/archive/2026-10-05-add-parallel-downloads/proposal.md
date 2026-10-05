## Why

The `sync` command downloads files one at a time. For a 1k-file public resource, the wall time is dominated by per-file round-trips. Adding `--parallel N` lets users opt into a thread pool and finish large backups faster.

## What Changes

- Add `--parallel N` (default `1`) option to the `sync` command.
- Thread-pool-based download: each item is downloaded in its own worker.
- Respect rate limits (`HTTP_TOO_MANY_REQUESTS` already throttles per-thread via `_request_with_backoff`).
- The HTTPAdapter pool size scales with the worker count so concurrent workers don't share connections.

## Capabilities

### Modified Capabilities
- `core-architecture`: The `sync` command MUST support parallel file downloads via `--parallel N`.

## Impact

- `ydiskarc/cmds/processor.py` — `yd_get_and_store_dir` accepts `parallel: int` and dispatches file downloads through a `ThreadPoolExecutor`.
- `ydiskarc/core.py` — add `--parallel` option to the `sync` Typer command.
- `ydiskarc/config.py` — add `pool_maxsize: int` so `HTTPAdapter(max_retries=..., pool_connections=N, pool_maxsize=N)` scales with the worker count.
- `tests/test_processor.py` — add a test that `--parallel 4` submits 4 download jobs for 4-file resource.