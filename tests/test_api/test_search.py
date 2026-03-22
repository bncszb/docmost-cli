"""Tests for Search API methods."""

from docmost_cli.api.client import DocmostClient
from docmost_cli.api.search import search


class TestSearch:
    def test_basic_search(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/search",
            json={"data": {"items": [
                {"id": "p1", "title": "Result Page", "highlight": "matched text"},
            ]}},
        )
        with DocmostClient(api_key_settings) as client:
            result = search(client, "test query")
        assert result["data"]["items"][0]["title"] == "Result Page"

    def test_search_with_filters(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/search",
            json={"data": {"items": []}},
        )
        with DocmostClient(api_key_settings) as client:
            search(client, "query", space_id="s1", result_type="page", limit=5)

        import json
        request = httpx_mock.get_requests()[0]
        body = json.loads(request.content)
        assert body["query"] == "query"
        assert body["spaceId"] == "s1"
        assert body["type"] == "page"
        assert body["limit"] == 5
