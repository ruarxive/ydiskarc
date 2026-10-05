## Why

`ydiskarc/downloader.py` parses `Content-Disposition` with a regex `re.findall("filename=(.+)", ...)` and decodes the bytes as latin-1 then utf-8. This is fragile in three ways:

1. **No RFC 5987 / `filename*=UTF-8''...` support.** Modern servers (including Yandex) emit `filename*` for non-ASCII filenames; the regex ignores them and falls back to the URL tail, which often has the wrong extension.
2. **Naive multi-value handling.** A response with both `filename=ASCII.pdf` and `filename*=UTF-8''...` returns whichever the regex grabs first.
4. **Header-injection surface.** The captured string is used directly as a filename; while not an injection point today, it becomes one if any future caller logs it without escaping.

## What Changes

- Replace the regex-based parser with a proper RFC 6266 / 5987 parser using Python's stdlib `email.message.Message` and `urllib.parse.unquote`.
- Prefer `filename*` over `filename` when both are supplied.
- Decode using the encoding declared in `filename*` (default UTF-8).
- Sanitize the resulting filename: strip CR/LF, drop NULs, reject control characters.
- Reject names containing path separators (`/`, `\`) by replacing them with `_`.

## Capabilities

### Modified Capabilities
- `core-architecture`: Filenames derived from server-supplied `Content-Disposition` headers MUST follow RFC 5987 (`filename*=`), and must be sanitized before use.

## Impact

- `ydiskarc/downloader.py` — replace `re.findall("filename=(.+)", ...)` with a new `_parse_content_disposition(header_value: str) -> Optional[str]` helper.
- New helper is unit-tested with several header shapes (ASCII, RFC 5987, both, missing).
- No runtime dependencies added.