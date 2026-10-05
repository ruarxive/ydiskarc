## Why

`downloader.py` hardcodes `verify=True` in every `session.get(...)` call. Users behind corporate proxies with a private CA cannot point at their CA bundle, and there is no env override.

## What Changes

- Add `verify: Optional[Union[bool, str]] = None` to `ydiskarc/config.py` `Config`.
- Read `YDISKARC_TLS_VERIFY` env var (or `REQUESTS_CA_BUNDLE`) at startup; pass through to the `requests` session.
- Replace the four `verify=True` literals in `downloader.py` with the configured value.

## Capabilities

### Modified Capabilities
- `core-architecture`: TLS verification MUST be configurable per-deployment (env var + `Config.verify`) so corporate proxies and self-hosted test fixtures work.

## Impact

- `ydiskarc/config.py` — add `verify` field.
- `ydiskarc/downloader.py` — pass `verify=config.verify` to `_probe` calls.
- `tests/test_config.py` — add tests for the new field.

## Notes

- Defaults preserve current behavior (`True` when no env var is set, `None` meaning "use `requests` defaults").
- `YDISKARC_TLS_VERIFY=0` disables verification (with a printed warning).