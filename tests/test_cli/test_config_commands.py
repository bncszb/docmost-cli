"""Tests for config CLI commands."""

from typer.testing import CliRunner

from docmost_cli.cli.main import app

runner = CliRunner()


class TestConfigShow:
    def test_show_with_config_file(self, tmp_config) -> None:
        result = runner.invoke(app, ["--config", str(tmp_config), "config", "show"])
        assert result.exit_code == 0
        assert "docs.example.com" in result.output
        # API key should be masked
        assert "dm_test1234567890" not in result.output
        assert "dm_t" in result.output  # First 4 chars visible

    def test_show_missing_config(self, tmp_path) -> None:
        config = tmp_path / "nonexistent.toml"
        result = runner.invoke(app, ["--config", str(config), "config", "show"])
        assert result.exit_code == 0


class TestConfigSet:
    def test_set_url(self, tmp_path) -> None:
        config = tmp_path / "config.toml"
        result = runner.invoke(
            app, ["--config", str(config), "config", "set", "url", "https://new.example.com"]
        )
        assert result.exit_code == 0

        # Verify by showing
        result = runner.invoke(app, ["--config", str(config), "config", "show"])
        assert "new.example.com" in result.output

    def test_set_invalid_key(self, tmp_path) -> None:
        config = tmp_path / "config.toml"
        result = runner.invoke(
            app, ["--config", str(config), "config", "set", "invalid_key", "value"]
        )
        assert result.exit_code != 0


class TestHelpOutput:
    def test_main_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "docmost-cli" in result.output.lower() or "CLI tool" in result.output

    def test_config_help(self) -> None:
        result = runner.invoke(app, ["config", "--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "show" in result.output
        assert "set" in result.output
        assert "test" in result.output
