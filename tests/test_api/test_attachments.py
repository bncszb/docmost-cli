"""Tests for Attachment API methods."""

from docmost_cli.api.attachments import search_attachments
from docmost_cli.api.client import DocmostClient


class TestSearchAttachments:
    def test_returns_results(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/attachments/search",
            json={
                "data": {
                    "items": [
                        {"id": "att-1", "fileName": "diagram.png", "type": "image/png"},
                        {"id": "att-2", "fileName": "report.pdf", "type": "application/pdf"},
                    ]
                }
            },
        )
        with DocmostClient(api_key_settings) as client:
            result = search_attachments(client, "diagram")
        items = result["data"]["items"]
        assert len(items) == 2
        assert items[0]["fileName"] == "diagram.png"

    def test_with_space_id_filter(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/attachments/search",
            json={
                "data": {
                    "items": [
                        {"id": "att-3", "fileName": "logo.svg", "type": "image/svg+xml"},
                    ]
                }
            },
        )
        with DocmostClient(api_key_settings) as client:
            result = search_attachments(client, "logo", space_id="space-abc")
        request = httpx_mock.get_requests()[0]
        body = request.read()
        assert b"spaceId" in body
        assert b"space-abc" in body
        items = result["data"]["items"]
        assert len(items) == 1
        assert items[0]["id"] == "att-3"
