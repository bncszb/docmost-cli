"""Tests for docmost_cli.sync.frontmatter module."""

from pathlib import Path

import pytest

from docmost_cli.sync.frontmatter import (
    parse_frontmatter,
    read_sync_file,
    serialize_frontmatter,
    write_sync_file,
)

# ---------------------------------------------------------------------------
# parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    """Tests for parse_frontmatter."""

    def test_normal_frontmatter(self) -> None:
        """Standard frontmatter with id, title, parent_id, icon."""
        text = (
            "---\n"
            "id: abc123\n"
            "title: My Page\n"
            "parent_id: def456\n"
            "icon: rocket\n"
            "---\n"
            "\n"
            "# Hello World\n"
        )
        meta, body = parse_frontmatter(text)
        assert meta == {
            "id": "abc123",
            "title": "My Page",
            "parent_id": "def456",
            "icon": "rocket",
        }
        assert body == "# Hello World\n"

    def test_no_frontmatter(self) -> None:
        """Plain markdown without frontmatter returns empty dict."""
        text = "# Just a heading\n\nSome content.\n"
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_empty_body_after_frontmatter(self) -> None:
        """Frontmatter with nothing after closing delimiter."""
        text = "---\nid: abc\n---\n"
        meta, body = parse_frontmatter(text)
        assert meta == {"id": "abc"}
        assert body == ""

    def test_value_containing_colon(self) -> None:
        """Colon inside value — split on first colon only."""
        text = "---\ntitle: AC/DC: The Best\n---\n\nContent.\n"
        meta, body = parse_frontmatter(text)
        assert meta["title"] == "AC/DC: The Best"

    def test_empty_value(self) -> None:
        """Key with no value after colon stores empty string."""
        text = "---\nicon:\n---\n\nBody.\n"
        meta, body = parse_frontmatter(text)
        assert meta["icon"] == ""

    def test_whitespace_around_keys_and_values(self) -> None:
        """Extra whitespace is stripped from keys and values."""
        text = "---\n  id  :  abc123  \n  title :  Spaced Out  \n---\n\nBody.\n"
        meta, body = parse_frontmatter(text)
        assert meta == {"id": "abc123", "title": "Spaced Out"}

    def test_multiple_dashes_in_body(self) -> None:
        """Only the first --- pair is treated as frontmatter."""
        text = "---\nid: abc\n---\n\nSome text.\n\n---\n\nMore text after horizontal rule.\n"
        meta, body = parse_frontmatter(text)
        assert meta == {"id": "abc"}
        assert "---" in body
        assert "More text after horizontal rule." in body

    def test_no_closing_delimiter(self) -> None:
        """Opening --- but no closing --- → treat as no frontmatter."""
        text = "---\nid: abc\ntitle: Oops\n"
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert body == text

    def test_empty_string(self) -> None:
        """Empty input returns empty dict and empty body."""
        meta, body = parse_frontmatter("")
        assert meta == {}
        assert body == ""

    def test_lines_without_colon_skipped(self) -> None:
        """Lines in frontmatter block that lack a colon are ignored."""
        text = "---\nid: abc\nno-colon-here\ntitle: Hi\n---\n\nBody.\n"
        meta, body = parse_frontmatter(text)
        assert meta == {"id": "abc", "title": "Hi"}

    def test_windows_line_endings(self) -> None:
        """Frontmatter with \\r\\n line endings is parsed correctly."""
        text = "---\r\nid: abc\r\ntitle: Win\r\n---\r\n\r\nBody.\r\n"
        meta, body = parse_frontmatter(text)
        assert meta == {"id": "abc", "title": "Win"}
        assert "Body." in body


# ---------------------------------------------------------------------------
# serialize_frontmatter
# ---------------------------------------------------------------------------


class TestSerializeFrontmatter:
    """Tests for serialize_frontmatter."""

    def test_normal_case(self) -> None:
        """Produces valid frontmatter with blank separator line."""
        meta = {"id": "abc", "title": "Hello"}
        body = "# Heading\n"
        result = serialize_frontmatter(meta, body)
        assert result == "---\nid: abc\ntitle: Hello\n---\n\n# Heading\n"

    def test_empty_metadata(self) -> None:
        """Empty dict still produces --- delimiters."""
        result = serialize_frontmatter({}, "Body.\n")
        assert result == "---\n---\n\nBody.\n"

    def test_field_ordering(self) -> None:
        """Known fields appear in fixed order regardless of dict insertion order."""
        meta = {"icon": "star", "title": "Z Title", "id": "abc", "parent_id": "p1"}
        result = serialize_frontmatter(meta, "")
        lines = result.split("\n")
        # lines[0] = '---', then known fields in order.
        assert lines[1] == "id: abc"
        assert lines[2] == "title: Z Title"
        assert lines[3] == "parent_id: p1"
        assert lines[4] == "icon: star"

    def test_unknown_fields_after_known(self) -> None:
        """Fields not in the known list appear after known fields."""
        meta = {"custom": "val", "id": "abc", "extra": "stuff"}
        result = serialize_frontmatter(meta, "")
        lines = result.split("\n")
        assert lines[1] == "id: abc"
        assert lines[2] == "custom: val"
        assert lines[3] == "extra: stuff"

    def test_empty_value_serialized(self) -> None:
        """Empty value is serialized as 'key: ' (trailing space is OK)."""
        result = serialize_frontmatter({"icon": ""}, "")
        assert "icon:" in result

    def test_roundtrip_serialize_then_parse(self) -> None:
        """Serialized output parses back to the same data."""
        meta = {"id": "abc", "title": "Hello", "icon": "star"}
        body = "Content here.\n"
        text = serialize_frontmatter(meta, body)
        parsed_meta, parsed_body = parse_frontmatter(text)
        assert parsed_meta == meta
        assert parsed_body == body


# ---------------------------------------------------------------------------
# Roundtrip tests
# ---------------------------------------------------------------------------


class TestRoundtrip:
    """Parse → serialize → parse roundtrip fidelity."""

    def test_basic_roundtrip(self) -> None:
        """Serialize then parse returns identical data."""
        meta = {"id": "x1", "title": "Test", "parent_id": "p1", "icon": "book"}
        body = "Some **bold** text.\n"
        text = serialize_frontmatter(meta, body)
        rt_meta, rt_body = parse_frontmatter(text)
        assert rt_meta == meta
        assert rt_body == body

    def test_unicode_german_umlauts(self) -> None:
        """German umlauts survive roundtrip."""
        meta = {"id": "u1", "title": "Über Änderungen: öffentlich und straße"}
        body = "Grüße aus München.\n"
        text = serialize_frontmatter(meta, body)
        rt_meta, rt_body = parse_frontmatter(text)
        assert rt_meta == meta
        assert rt_body == body

    def test_unicode_emoji(self) -> None:
        """Emoji content survives roundtrip."""
        meta = {"id": "e1", "title": "Status Report", "icon": "📊"}
        body = "All tasks done ✅\n"
        text = serialize_frontmatter(meta, body)
        rt_meta, rt_body = parse_frontmatter(text)
        assert rt_meta == meta
        assert rt_body == body

    def test_multiline_body(self) -> None:
        """Multi-paragraph body preserved exactly."""
        meta = {"id": "m1"}
        body = "# Heading\n\nParagraph one.\n\nParagraph two.\n"
        text = serialize_frontmatter(meta, body)
        rt_meta, rt_body = parse_frontmatter(text)
        assert rt_meta == meta
        assert rt_body == body


# ---------------------------------------------------------------------------
# read_sync_file / write_sync_file
# ---------------------------------------------------------------------------


class TestFileIO:
    """Tests for read_sync_file and write_sync_file."""

    def test_write_then_read(self, tmp_path: Path) -> None:
        """Write and read back returns same metadata and body."""
        filepath = tmp_path / "page.md"
        meta = {"id": "abc", "title": "My Page"}
        body = "Hello world.\n"
        write_sync_file(filepath, meta, body)
        rt_meta, rt_body = read_sync_file(filepath)
        assert rt_meta == meta
        assert rt_body == body

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """write_sync_file creates missing parent dirs."""
        filepath = tmp_path / "deep" / "nested" / "dir" / "page.md"
        write_sync_file(filepath, {"id": "abc"}, "Body.\n")
        assert filepath.exists()
        meta, body = read_sync_file(filepath)
        assert meta["id"] == "abc"

    def test_read_nonexistent_raises(self, tmp_path: Path) -> None:
        """Reading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            read_sync_file(tmp_path / "nope.md")

    def test_utf8_preserved(self, tmp_path: Path) -> None:
        """UTF-8 content (umlauts, emoji) survives write → read."""
        filepath = tmp_path / "unicode.md"
        meta = {"id": "u1", "title": "Ärger mit Ü"}
        body = "Straße 📊 ✅\n"
        write_sync_file(filepath, meta, body)
        rt_meta, rt_body = read_sync_file(filepath)
        assert rt_meta == meta
        assert rt_body == body

    def test_file_content_is_valid_frontmatter_format(self, tmp_path: Path) -> None:
        """Written file content starts with --- and has expected structure."""
        filepath = tmp_path / "check.md"
        write_sync_file(filepath, {"id": "abc", "title": "T"}, "Body.\n")
        raw = filepath.read_text(encoding="utf-8")
        assert raw.startswith("---\n")
        assert "\n---\n" in raw


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge-case behaviour."""

    def test_body_with_leading_newlines(self) -> None:
        """Leading blank lines in the body are preserved after the separator."""
        meta = {"id": "abc"}
        body = "\n\nStarting with blanks.\n"
        text = serialize_frontmatter(meta, body)
        rt_meta, rt_body = parse_frontmatter(text)
        assert rt_meta == meta
        assert rt_body == body

    def test_body_is_empty_string(self) -> None:
        """Empty body roundtrips cleanly."""
        meta = {"id": "abc"}
        body = ""
        text = serialize_frontmatter(meta, body)
        rt_meta, rt_body = parse_frontmatter(text)
        assert rt_meta == meta
        assert rt_body == body

    def test_only_delimiters(self) -> None:
        """File that is just two --- lines."""
        text = "---\n---\n"
        meta, body = parse_frontmatter(text)
        assert meta == {}
        assert body == ""

    def test_value_with_leading_spaces_preserved(self) -> None:
        """Colons with spaces — value is still stripped."""
        text = "---\ntitle:   lots of spaces   \n---\n\nBody.\n"
        meta, _ = parse_frontmatter(text)
        assert meta["title"] == "lots of spaces"
