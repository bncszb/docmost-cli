"""Tests for user CLI commands."""

from typer.testing import CliRunner

from docmost_cli.cli.main import app

runner = CliRunner()


class TestUserMe:
    def test_shows_key_value_output(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/users/me",
            json={
                "data": {
                    "id": "user-42",
                    "email": "alice@example.com",
                    "name": "Alice",
                    "role": "admin",
                    "createdAt": "2025-06-15T10:30:00Z",
                }
            },
        )
        result = runner.invoke(app, ["--config", str(tmp_config), "user", "me"])
        assert result.exit_code == 0
        assert "alice@example.com" in result.output
        assert "Alice" in result.output
        assert "user-42" in result.output
