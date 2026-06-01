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


class TestSpaceExport:
    def test_export(self, tmp_config, httpx_mock, tmp_path) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces",
            json={"data": {"items": [{"id": "space-123", "slug": "eng", "name": "Eng"}]}},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces/export",
            content=b"PK\x03\x04zipdata",
        )

        out_file = tmp_path / "export.zip"
        result = runner.invoke(
            app,
            [
                "--config", str(tmp_config),
                "space", "export",
                "eng",
                "--output", str(out_file),
                "--format", "markdown",
                "--include-attachments"
            ]
        )
        assert result.exit_code == 0
        assert out_file.exists()
        assert out_file.read_bytes() == b"PK\x03\x04zipdata"

    def test_export_invalid_format(self, tmp_config) -> None:
        result = runner.invoke(
            app,
            [
                "--config", str(tmp_config),
                "space", "export",
                "eng",
                "--output", "test.zip",
                "--format", "pdf"
            ]
        )
        assert result.exit_code != 0
        assert "Format must be 'html' or 'markdown'" in result.output
