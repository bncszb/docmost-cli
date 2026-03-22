"""Tests for DocmostSettings."""

import pytest

from docmost_cli.config.settings import DocmostSettings


class TestDocmostSettings:
    def test_defaults(self) -> None:
        settings = DocmostSettings()
        assert settings.url is None
        assert settings.api_key is None
        assert settings.email is None
        assert settings.password is None
        assert settings.profile == "default"

    def test_explicit_values(self) -> None:
        settings = DocmostSettings(
            url="https://example.com",
            api_key="dm_abc123",
        )
        assert settings.url == "https://example.com"
        assert settings.api_key == "dm_abc123"

    def test_env_var_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DOCMOST_URL", "https://from-env.example.com")
        monkeypatch.setenv("DOCMOST_API_KEY", "dm_envkey")
        settings = DocmostSettings()
        assert settings.url == "https://from-env.example.com"
        assert settings.api_key == "dm_envkey"

    def test_init_kwargs_beat_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """In pydantic-settings v2, init kwargs have highest priority."""
        monkeypatch.setenv("DOCMOST_URL", "https://env-value.example.com")
        settings = DocmostSettings(url="https://init-wins.example.com")
        assert settings.url == "https://init-wins.example.com"
