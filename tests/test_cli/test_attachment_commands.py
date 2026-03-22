"""Tests for attachment CLI commands."""

from typer.testing import CliRunner

from docmost_cli.cli.main import app

runner = CliRunner()


class TestAttachmentSearch:
    def test_search_json(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/attachments/search",
            json={
                "data": {
                    "items": [
                        {"id": "att-1", "fileName": "diagram.png", "type": "image/png"},
                        {"id": "att-2", "fileName": "screenshot.jpg", "type": "image/jpeg"},
                    ]
                }
            },
        )
        result = runner.invoke(
            app,
            ["--config", str(tmp_config), "attachment", "search", "diagram", "--json"],
        )
        assert result.exit_code == 0
        assert "att-1" in result.output
        assert "diagram.png" in result.output
        assert "att-2" in result.output

    def test_search_with_space(self, tmp_config, httpx_mock) -> None:
        # First call resolves space slug to ID
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces/info",
            json={"id": "space-uuid", "slug": "eng"},
        )
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
        result = runner.invoke(
            app,
            [
                "--config", str(tmp_config),
                "attachment", "search", "logo",
                "--space", "eng",
                "--json",
            ],
        )
        assert result.exit_code == 0
        assert "att-3" in result.output
        assert "logo.svg" in result.output
