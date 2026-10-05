## 1. Implementation

- [ ] 1.1 Add `YandexDiskClient._request_with_backoff(self, method, url, **kwargs)` returning `requests.Response`.
- [ ] 1.2 Rewrite `get_resource_metadata` to call `_request_with_backoff("GET", self.api_url, params=params, timeout=config.timeout)`.
- [ ] 1.3 Rewrite `get_download_link` similarly.
- [ ] 1.4 In `downloader.get_file`, replace the inline initial probe and resume probe with calls to a shared helper (either `client._request_with_backoff` or a module-level function in `downloader.py`).
- [ ] 1.5 Add a regression test in `tests/test_processor.py` that mocks `session.get` to return 429 once then 200, asserts `handle_rate_limit` was called and the final response is the 200.

## 2. Validation

- [ ] 2.1 `pytest -q` passes.
- [ ] 2.2 No behavior change visible to users; existing tests for `get_resource_metadata` and `get_download_link` still pass.