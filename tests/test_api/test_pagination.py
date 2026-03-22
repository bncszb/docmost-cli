"""Tests for pagination utilities."""

from docmost_cli.api.pagination import extract_items, get_cursor


class TestExtractItems:
    def test_data_items_shape(self) -> None:
        response = {"data": {"items": [{"id": "1"}, {"id": "2"}]}}
        result = extract_items(response)
        assert result == [{"id": "1"}, {"id": "2"}]

    def test_data_list_shape(self) -> None:
        response = {"data": [{"id": "a"}, {"id": "b"}]}
        result = extract_items(response)
        assert result == [{"id": "a"}, {"id": "b"}]

    def test_items_shape(self) -> None:
        response = {"items": [{"id": "x"}, {"id": "y"}]}
        result = extract_items(response)
        assert result == [{"id": "x"}, {"id": "y"}]

    def test_flat_dict_shape(self) -> None:
        response = {"id": "flat-123", "name": "Single Item"}
        result = extract_items(response)
        assert result == [{"id": "flat-123", "name": "Single Item"}]

    def test_empty_data_items(self) -> None:
        response = {"data": {"items": []}}
        result = extract_items(response)
        assert result == []

    def test_no_items_no_id(self) -> None:
        response = {"status": "ok"}
        result = extract_items(response)
        assert result == []


class TestGetCursor:
    def test_nested_cursor(self) -> None:
        response = {"data": {"items": [], "cursor": "abc123"}}
        cursor = get_cursor(response)
        assert cursor == "abc123"

    def test_top_level_cursor(self) -> None:
        response = {"items": [], "cursor": "next-page"}
        cursor = get_cursor(response)
        assert cursor == "next-page"

    def test_returns_none_when_no_cursor(self) -> None:
        response = {"data": {"items": []}}
        cursor = get_cursor(response)
        assert cursor is None

    def test_returns_none_for_empty_response(self) -> None:
        response = {}
        cursor = get_cursor(response)
        assert cursor is None

    def test_returns_none_when_cursor_is_none(self) -> None:
        response = {"data": {"items": [], "cursor": None}}
        cursor = get_cursor(response)
        assert cursor is None
