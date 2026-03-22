"""Tests for space CLI commands."""

from typer.testing import CliRunner

from docmost_cli.cli.main import app

runner = CliRunner()


class TestSpaceList:
    def test_list_json(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces",
            json={
                "data": {
                    "items": [
                        {"id": "s1", "name": "Engineering", "slug": "eng", "description": ""},
                    ]
                }
            },
        )
        result = runner.invoke(app, ["--config", str(tmp_config), "space", "list", "--json"])
        assert result.exit_code == 0
        assert "eng" in result.output
        assert "s1" in result.output

    def test_list_table(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces",
            json={
                "data": {
                    "items": [
                        {"id": "s1", "name": "Engineering", "slug": "eng", "description": ""},
                    ]
                }
            },
        )
        result = runner.invoke(app, ["--config", str(tmp_config), "space", "list"])
        assert result.exit_code == 0
        assert "Engineering" in result.output


class TestSpaceCreate:
    def test_create(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces/create",
            json={"id": "new-space", "name": "Test", "slug": "test"},
        )
        result = runner.invoke(
            app, ["--config", str(tmp_config), "space", "create", "--name", "Test"]
        )
        assert result.exit_code == 0
        assert "new-space" in result.output


class TestSpaceUpdate:
    def test_update(self, tmp_config, httpx_mock) -> None:
        # First resolves slug to ID via listing all spaces
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces",
            json={"data": {"items": [{"id": "space-123", "slug": "eng", "name": "Eng"}]}},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces/update",
            json={"id": "space-123", "name": "Updated"},
        )
        result = runner.invoke(
            app,
            ["--config", str(tmp_config), "space", "update", "eng", "--name", "Updated"],
        )
        assert result.exit_code == 0
        assert "space-123" in result.output

    def test_update_no_flags(self, tmp_config) -> None:
        result = runner.invoke(app, ["--config", str(tmp_config), "space", "update", "eng"])
        assert result.exit_code != 0
