"""Tests for Comment API methods."""

from docmost_cli.api.client import DocmostClient
from docmost_cli.api.comments import (
    _wrap_text_as_prosemirror,
    create_comment,
    list_comments,
    update_comment,
)


class TestWrapTextAsProsemirror:
    def test_single_line(self) -> None:
        result = _wrap_text_as_prosemirror("Hello world")
        assert result["type"] == "doc"
        assert len(result["content"]) == 1
        assert result["content"][0]["type"] == "paragraph"
        assert result["content"][0]["content"][0]["text"] == "Hello world"

    def test_multiline(self) -> None:
        result = _wrap_text_as_prosemirror("Line 1\nLine 2")
        assert len(result["content"]) == 2
        assert result["content"][0]["content"][0]["text"] == "Line 1"
        assert result["content"][1]["content"][0]["text"] == "Line 2"

    def test_with_blank_lines(self) -> None:
        result = _wrap_text_as_prosemirror("Para 1\n\nPara 2")
        assert len(result["content"]) == 3
        # Middle paragraph is empty (blank line)
        assert "content" not in result["content"][1]


class TestListComments:
    def test_returns_comments(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/comments",
            json={"data": [{"id": "c1", "content": {"type": "doc", "content": []}}]},
        )
        with DocmostClient(api_key_settings) as client:
            result = list_comments(client, "page-1")
        assert result["data"][0]["id"] == "c1"


class TestCreateComment:
    def test_creates_comment(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/comments/create",
            json={"id": "new-comment"},
        )
        with DocmostClient(api_key_settings) as client:
            result = create_comment(client, page_id="page-1", content="Great work!")
        assert result["id"] == "new-comment"

        # Verify ProseMirror wrapping was applied (content is JSON-stringified)
        import json

        request = httpx_mock.get_requests()[0]
        body = json.loads(request.content)
        content = json.loads(body["content"])
        assert content["type"] == "doc"
        assert content["content"][0]["content"][0]["text"] == "Great work!"


class TestUpdateComment:
    def test_updates_comment(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/comments/update",
            json={"id": "c1"},
        )
        with DocmostClient(api_key_settings) as client:
            result = update_comment(client, comment_id="c1", content="Updated text")
        assert result["id"] == "c1"
