"""Tests for Page API methods."""

import pytest

from docmost_cli.api.client import DocmostClient
from docmost_cli.api.pages import (
    create_page_via_import,
    delete_page,
    get_page_content,
    get_page_info,
    list_recent_pages,
    move_page,
    update_page_content,
    update_page_meta,
)


class TestGetPageInfo:
    def test_returns_info(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/info",
            json={"id": "page-1", "title": "Test Page", "spaceId": "s1"},
        )
        with DocmostClient(api_key_settings) as client:
            result = get_page_info(client, "page-1")
        assert result["title"] == "Test Page"

    def test_not_found(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/info",
            status_code=404,
        )
        with DocmostClient(api_key_settings) as client, pytest.raises(SystemExit) as exc:
            get_page_info(client, "nonexistent")
        assert exc.value.code == 4


class TestCreatePageViaImport:
    def test_sends_multipart(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/import",
            json={"id": "new-page"},
        )
        with DocmostClient(api_key_settings) as client:
            result = create_page_via_import(
                client,
                space_id="space-1",
                title="New Page",
                content="Hello world",
            )
        assert result["id"] == "new-page"

        # Verify the request was sent
        request = httpx_mock.get_requests()[0]
        assert request.method == "POST"

    def test_empty_content(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/import",
            json={"id": "empty-page"},
        )
        with DocmostClient(api_key_settings) as client:
            result = create_page_via_import(
                client,
                space_id="space-1",
                title="Empty Page",
                content="",
            )
        assert result["id"] == "empty-page"

    def test_with_parent(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/import",
            json={"id": "child-page"},
        )
        with DocmostClient(api_key_settings) as client:
            result = create_page_via_import(
                client,
                space_id="space-1",
                title="Child",
                content="Content",
                parent_page_id="parent-1",
            )
        assert result["id"] == "child-page"


class TestUpdatePageMeta:
    def test_update_title(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/update",
            json={"id": "page-1", "title": "New Title"},
        )
        with DocmostClient(api_key_settings) as client:
            result = update_page_meta(client, page_id="page-1", title="New Title")
        assert result["title"] == "New Title"


class TestUpdatePageContent:
    def test_sends_content(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/content/update",
            json={"success": True},
        )
        with DocmostClient(api_key_settings) as client:
            result = update_page_content(
                client, page_id="page-1", content="# Updated\n\nNew content"
            )
        assert result["success"] is True

    def test_enterprise_only_404(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/content/update",
            status_code=404,
        )
        with DocmostClient(api_key_settings) as client, pytest.raises(SystemExit) as exc:
            update_page_content(client, page_id="page-1", content="test")
        assert exc.value.code == 1  # Re-raised with helpful message


class TestDeletePage:
    def test_deletes(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/delete",
            json={"id": "page-1"},
        )
        with DocmostClient(api_key_settings) as client:
            result = delete_page(client, "page-1")
        assert result["id"] == "page-1"


class TestMovePage:
    def test_move_to_parent(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/move",
            json={"id": "page-1"},
        )
        with DocmostClient(api_key_settings) as client:
            result = move_page(client, page_id="page-1", parent_page_id="parent-1")
        assert result["id"] == "page-1"

    def test_move_to_space(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/move",
            json={"id": "page-1"},
        )
        with DocmostClient(api_key_settings) as client:
            result = move_page(client, page_id="page-1", space_id="space-2")
        assert result["id"] == "page-1"


class TestGetPageContent:
    def test_enterprise_content_endpoint(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/content",
            json={"content": {"type": "doc", "content": []}},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/info",
            json={"id": "page-1", "title": "Test", "spaceId": "s1"},
        )
        with DocmostClient(api_key_settings) as client:
            result = get_page_content(client, "page-1")
        assert result["id"] == "page-1"
        assert "content" in result

    def test_fallback_to_info(self, httpx_mock, api_key_settings) -> None:
        # Content endpoint returns 404 (Community edition)
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/content",
            status_code=404,
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/info",
            json={"id": "page-1", "title": "Test", "content": {"type": "doc", "content": []}},
        )
        with DocmostClient(api_key_settings) as client:
            result = get_page_content(client, "page-1")
        assert result["id"] == "page-1"


class TestListRecentPages:
    def test_list_pages(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/recent",
            json={"data": {"items": [
                {"id": "p1", "title": "Page 1", "updatedAt": "2026-03-20"},
            ]}},
        )
        with DocmostClient(api_key_settings) as client:
            result = list_recent_pages(client, "space-1")
        assert result["data"]["items"][0]["title"] == "Page 1"
