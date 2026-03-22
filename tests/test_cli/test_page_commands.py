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


class TestPageList:
    def test_list_json(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces/info",
            json={"id": "s1", "slug": "eng"},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/recent",
            json={"data": {"items": [
                {"id": "p1", "title": "Page One", "updatedAt": "2026-03-20"},
            ]}},
        )
        result = runner.invoke(
            app, ["--config", str(tmp_config), "page", "list", "eng", "--json"]
        )
        assert result.exit_code == 0
        assert "Page One" in result.output
        assert "p1" in result.output

    def test_list_table(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/spaces/info",
            json={"id": "s1", "slug": "eng"},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/recent",
            json={"data": {"items": [
                {"id": "p1", "title": "Page One", "updatedAt": "2026-03-20"},
            ]}},
        )
        result = runner.invoke(
            app, ["--config", str(tmp_config), "page", "list", "eng"]
        )
        assert result.exit_code == 0
        assert "Page One" in result.output


class TestPageGet:
    def test_get_markdown(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/content",
            json={"content": {
                "type": "doc",
                "content": [
                    {"type": "heading", "attrs": {"level": 1},
                     "content": [{"type": "text", "text": "Hello"}]},
                    {"type": "paragraph",
                     "content": [{"type": "text", "text": "World"}]},
                ],
            }},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/info",
            json={"id": "page-1", "title": "Hello", "spaceId": "s1"},
        )
        result = runner.invoke(
            app, ["--config", str(tmp_config), "page", "get", "page-1"]
        )
        assert result.exit_code == 0
        assert "# Hello" in result.output
        assert "World" in result.output

    def test_get_raw(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/content",
            json={"content": {"type": "doc", "content": []}},
        )
        result = runner.invoke(
            app, ["--config", str(tmp_config), "page", "get", "page-1", "--raw"]
        )
        assert result.exit_code == 0
        assert '"type"' in result.output

    def test_get_meta(self, tmp_config, httpx_mock) -> None:
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/content",
            json={"content": {
                "type": "doc",
                "content": [
                    {"type": "paragraph",
                     "content": [{"type": "text", "text": "Content"}]},
                ],
            }},
        )
        httpx_mock.add_response(
            url="https://docs.example.com/api/pages/info",
            json={"id": "page-1", "title": "Test", "spaceId": "s1",
                  "createdAt": "2026-01-01", "updatedAt": "2026-03-20"},
        )
        result = runner.invoke(
            app, ["--config", str(tmp_config), "page", "get", "page-1", "--meta"]
        )
        assert result.exit_code == 0
        assert "---" in result.output
        assert "id: page-1" in result.output
        assert "Content" in result.output
