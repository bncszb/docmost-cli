"""Tests for page CLI commands."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from docmost_cli.cli.main import app
from docmost_cli.cli.page import _resolve_content

runner = CliRunner()


class TestResolveContent:
    def test_inline_content(self) -> None:
        result = _resolve_content("hello", None, False)
        assert result == "hello"

    def test_file_content(self, tmp_path: Path) -> None:
        f = tmp_path / "test.md"
        f.write_text("# File Content")
        result = _resolve_content(None, f, False)
        assert result == "# File Content"

    def test_no_content(self) -> None:
        result = _resolve_content(None, None, False)
        assert result is None

    def test_multiple_sources_exits(self) -> None:
        with pytest.raises(SystemExit):
            _resolve_content("inline", Path("file.md"), False)

    def test_file_not_found_exits(self) -> None:
        with pytest.raises(SystemExit):
            _resolve_content(None, Path("/nonexistent/file.md"), False)


class TestPageCreate:
    def test_create_with_content(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces/info",
            json={"id": "space-1", "slug": "eng"},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/import",
            json={"id": "page-new"},
        )
        result = runner.invoke(
            app,
            [
                "--config", str(tmp_config),
                "page", "create", "eng",
                "--title", "Test Page",
                "--content", "Hello world",
            ],
        )
        assert result.exit_code == 0
        assert "page-new" in result.output

    def test_create_empty_page(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces/info",
            json={"id": "space-1", "slug": "eng"},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/import",
            json={"id": "empty-page"},
        )
        result = runner.invoke(
            app,
            ["--config", str(tmp_config), "page", "create", "eng", "--title", "Empty"],
        )
        assert result.exit_code == 0
        assert "empty-page" in result.output

    def test_create_from_file(self, tmp_config, tmp_path, httpx_mock) -> None:
        content_file = tmp_path / "content.md"
        content_file.write_text("# From File\n\nContent here")

        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces/info",
            json={"id": "space-1", "slug": "eng"},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/import",
            json={"id": "file-page"},
        )
        result = runner.invoke(
            app,
            [
                "--config", str(tmp_config),
                "page", "create", "eng",
                "--title", "File Page",
                "--file", str(content_file),
            ],
        )
        assert result.exit_code == 0
        assert "file-page" in result.output


class TestPageUpdate:
    def test_update_title(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/info",
            json={"id": "page-1", "title": "Old Title"},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/update",
            json={"id": "page-1", "title": "New Title"},
        )
        result = runner.invoke(
            app,
            ["--config", str(tmp_config), "page", "update", "page-1", "--title", "New Title"],
        )
        assert result.exit_code == 0
        assert "page-1" in result.output

    def test_update_no_flags(self, tmp_config) -> None:
        result = runner.invoke(
            app, ["--config", str(tmp_config), "page", "update", "page-1"]
        )
        assert result.exit_code != 0


class TestPageDelete:
    def test_delete_with_yes(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/info",
            json={"id": "page-1", "title": "Doomed Page"},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/delete",
            json={"id": "page-1"},
        )
        result = runner.invoke(
            app, ["--config", str(tmp_config), "-y", "page", "delete", "page-1"]
        )
        assert result.exit_code == 0
        assert "page-1" in result.output

    def test_delete_aborted(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/info",
            json={"id": "page-1", "title": "Safe Page"},
        )
        result = runner.invoke(
            app,
            ["--config", str(tmp_config), "page", "delete", "page-1"],
            input="n\n",
        )
        assert result.exit_code != 0  # Aborted


class TestPageMove:
    def test_move_to_space(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces/info",
            json={"id": "space-2", "slug": "staging"},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/move",
            json={"id": "page-1"},
        )
        result = runner.invoke(
            app,
            ["--config", str(tmp_config), "page", "move", "page-1", "--space", "staging"],
        )
        assert result.exit_code == 0
        assert "page-1" in result.output

    def test_move_no_flags(self, tmp_config) -> None:
        result = runner.invoke(
            app, ["--config", str(tmp_config), "page", "move", "page-1"]
        )
        assert result.exit_code != 0
