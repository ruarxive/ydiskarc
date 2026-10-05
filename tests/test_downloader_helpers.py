"""Tests for Content-Disposition parsing and filename sanitization.

See openspec/changes/harden-content-disposition-parsing.
"""

from ydiskarc.downloader import parse_content_disposition, sanitize_filename


class TestParseContentDisposition:
    def test_plain_ascii_filename(self):
        result = parse_content_disposition("attachment; filename=hello.pdf")
        assert result == "hello.pdf"

    def test_quoted_filename_with_spaces(self):
        result = parse_content_disposition('attachment; filename="hello world.pdf"')
        assert result == "hello world.pdf"

    def test_rfc_5987_utf8_filename(self):
        # "Пример.pdf" URL-encoded as UTF-8.
        header = "attachment; filename*=UTF-8''%D0%9F%D1%80%D0%B8%D0%BC%D0%B5%D1%80.pdf"
        result = parse_content_disposition(header)
        assert result == "Пример.pdf"

    def test_filename_star_preferred_over_filename(self):
        header = "attachment; filename=fallback.pdf; filename*=UTF-8''actual.pdf"
        result = parse_content_disposition(header)
        assert result == "actual.pdf"

    def test_no_filename_returns_none(self):
        assert parse_content_disposition("inline") is None

    def test_empty_header_returns_none(self):
        assert parse_content_disposition("") is None
        assert parse_content_disposition(None) is None

    def test_inline_disposition(self):
        assert parse_content_disposition("inline; filename=preview.jpg") == "preview.jpg"

    def test_invalid_header_does_not_crash(self):
        # Garbage header value.
        assert parse_content_disposition("@@@not-a-valid-header@@@") is None or isinstance(
            parse_content_disposition("@@@not-a-valid-header@@@"), str
        )


class TestSanitizeFilename:
    def test_normal_name_unchanged(self):
        assert sanitize_filename("report.pdf") == "report.pdf"

    def test_strips_surrounding_quotes(self):
        assert sanitize_filename('"report.pdf"') == "report.pdf"
        assert sanitize_filename("'report.pdf'") == "report.pdf"

    def test_replaces_forward_slash(self):
        assert sanitize_filename("dir/file.pdf") == "dir_file.pdf"

    def test_replaces_backslash(self):
        assert sanitize_filename("dir\\file.pdf") == "dir_file.pdf"

    def test_strips_cr_lf(self):
        assert sanitize_filename("report\r\nX.pdf") == "reportX.pdf"

    def test_strips_nul(self):
        assert sanitize_filename("report\x00.pdf") == "report.pdf"

    def test_empty_string(self):
        assert sanitize_filename("") == ""

    def test_only_separators_returns_empty(self):
        assert sanitize_filename("///") == "___" or sanitize_filename("///") == ""
