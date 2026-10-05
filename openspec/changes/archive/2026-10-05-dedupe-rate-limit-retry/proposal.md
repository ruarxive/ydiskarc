## Why

The pattern
```
resp = session.get(url, ...)
if resp.status_code == 429:
    handle_rate_limit(resp)
    resp = session.get(url, ...)
resp.raise_for_status()
```
appears three times: `ydiskarc/client.py:67-72`, `ydiskarc/client.py:77-84`, and twice inside `ydiskarc/downloader.py:51-68, 113-131`. Each duplicate risks drift (one copy eventually adds backoff params, one forgets to call `raise_for_status`, etc.) and clutters the call sites. See `dev/docs/ANALYSIS_AND_IMPROVEMENTS.md` §3.1.

## What Changes

- Add a single `_request_with_backoff(method, url, **kwargs)` method to `YandexDiskClient` that:
  1. Issues the request.
  2. On `429`, calls `handle_rate_limit` and reissues once.
  3. Always calls `raise_for_status()` before returning.
- Replace the three duplicated blocks with calls to this helper.
- `downloader.get_file` keeps ownership of the streaming response (it needs `iter_content`), but the initial probe request and the resume-probe request route through the same helper.

## Capabilities

### Modified Capabilities
- `core-architecture`: HTTP request retry/backoff behavior MUST be implemented in a single place.

## Impact

- `ydiskarc/client.py` — add `_request_with_backoff`, simplify `get_resource_metadata` and `get_download_link`.
- `ydiskarc/downloader.py` — route the initial probe and resume probe through `client._request_with_backoff` (or a free function) instead of the inlined pattern.
- No public-API breakage.
- No runtime dependencies changed.