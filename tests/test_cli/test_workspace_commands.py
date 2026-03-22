"""Tests for workspace CLI commands."""

from typer.testing import CliRunner

from docmost_cli.cli.main import app

runner = CliRunner()


class TestWorkspaceInfo:
    def test_shows_key_value_output(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/workspace/info",
            json={
                "data": {
                    "id": "ws-1",
                    "name": "Acme Wiki",
                    "description": "Company wiki",
                    "memberCount": 12,
                    "createdAt": "2025-01-01T00:00:00Z",
                }
            },
        )
        result = runner.invoke(app, ["--config", str(tmp_config), "workspace", "info"])
        assert result.exit_code == 0
        assert "Acme Wiki" in result.output
        assert "ws-1" in result.output


class TestWorkspaceMembers:
    def test_members_json(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/workspace/members",
            json={
                "data": {
                    "items": [
                        {"id": "u1", "email": "alice@example.com",
                         "name": "Alice", "role": "admin"},
                        {"id": "u2", "email": "bob@example.com",
                         "name": "Bob", "role": "member"},
                    ]
                }
            },
        )
        result = runner.invoke(
            app, ["--config", str(tmp_config), "workspace", "members", "--json"]
        )
        assert result.exit_code == 0
        assert "alice@example.com" in result.output
        assert "bob@example.com" in result.output
        assert "u1" in result.output
        assert "u2" in result.output
