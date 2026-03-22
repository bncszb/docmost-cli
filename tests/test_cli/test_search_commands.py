"""Tests for search CLI command."""

from typer.testing import CliRunner

from docmost_cli.cli.main import app

runner = CliRunner()


class TestSearchCommand:
    def test_search_json(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/search",
            json={
                "data": {
                    "items": [
                        {"id": "p1", "title": "Found Page", "highlight": "match context"},
                    ]
                }
            },
        )
        result = runner.invoke(
            app, ["--config", str(tmp_config), "search", "query", "test", "--json"]
        )
        assert result.exit_code == 0
        assert "Found Page" in result.output

    def test_search_with_space_filter(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces",
            json={"data": {"items": [{"id": "s1", "slug": "eng", "name": "Eng"}]}},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/search",
            json={"data": {"items": []}},
        )
        result = runner.invoke(
            app,
            ["--config", str(tmp_config), "search", "query", "test", "--space", "eng", "--json"],
        )
        assert result.exit_code == 0
