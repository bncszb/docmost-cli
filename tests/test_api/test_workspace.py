"""Tests for Workspace API methods."""

from docmost_cli.api.client import DocmostClient
from docmost_cli.api.workspace import get_workspace_info, list_workspace_members


class TestGetWorkspaceInfo:
    def test_returns_data(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/workspace/info",
            json={
                "data": {
                    "id": "ws-1",
                    "name": "My Workspace",
                    "description": "A test workspace",
                    "memberCount": 5,
                }
            },
        )
        with DocmostClient(api_key_settings) as client:
            result = get_workspace_info(client)
        assert result["data"]["name"] == "My Workspace"
        assert result["data"]["memberCount"] == 5


class TestListWorkspaceMembers:
    def test_returns_items(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/workspace/members",
            json={
                "data": {
                    "items": [
                        {
                            "id": "u1",
                            "email": "alice@example.com",
                            "name": "Alice",
                            "role": "admin",
                        },
                        {"id": "u2", "email": "bob@example.com", "name": "Bob", "role": "member"},
                    ]
                }
            },
        )
        with DocmostClient(api_key_settings) as client:
            result = list_workspace_members(client)
        items = result["data"]["items"]
        assert len(items) == 2
        assert items[0]["email"] == "alice@example.com"
        assert items[1]["role"] == "member"

    def test_with_limit(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/workspace/members",
            json={"data": {"items": [], "cursor": None}},
        )
        with DocmostClient(api_key_settings) as client:
            list_workspace_members(client, limit=5)
        request = httpx_mock.get_requests()[0]
        body = request.read()
        assert b'"limit":5' in body or b'"limit": 5' in body
