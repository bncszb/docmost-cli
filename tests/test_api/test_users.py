"""Tests for User API methods."""

from docmost_cli.api.client import DocmostClient
from docmost_cli.api.users import get_current_user


class TestGetCurrentUser:
    def test_returns_user_data(self, httpx_mock, api_key_settings) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/users/me",
            json={
                "data": {
                    "id": "user-42",
                    "email": "alice@example.com",
                    "name": "Alice",
                    "role": "admin",
                    "createdAt": "2025-01-01T00:00:00Z",
                }
            },
        )
        with DocmostClient(api_key_settings) as client:
            result = get_current_user(client)
        assert result["id"] == "user-42"
        assert result["email"] == "alice@example.com"
        assert result["name"] == "Alice"
        assert result["role"] == "admin"
