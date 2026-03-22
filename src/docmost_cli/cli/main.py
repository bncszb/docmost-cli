"""Top-level typer app with global options and subcommand registration."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import typer

from docmost_cli.api.client import DocmostClient
from docmost_cli.config.store import load_settings
from docmost_cli.output.formatter import print_error

if TYPE_CHECKING:
    from docmost_cli.config.settings import DocmostSettings

__all__ = ["_ensure_utf8_stdio", "app", "get_client", "state"]


class State:
    """Global state shared across subcommands."""

    def __init__(self) -> None:
        self.settings: DocmostSettings | None = None
        self.client: DocmostClient | None = None
        self.config_path: Path | None = None
        self.verbose: bool = False
        self.yes: bool = False


state = State()

app = typer.Typer(
    name="docmost-cli",
    help="CLI tool for managing Docmost wiki instances.",
    no_args_is_help=True,
)


def _ensure_utf8_stdio() -> None:
    """Reconfigure stdout/stderr to UTF-8 on Windows.

    Needed so emoji and Rich box-drawing chars work on cp1252 consoles.
    Also called in __main__.py for 'python -m docmost_cli' invocation.
    """
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


@app.callback()
def main(
    profile: str = typer.Option("default", "--profile", "-p", help="Config profile name"),
    url: str | None = typer.Option(None, "--url", help="Override Docmost URL"),
    api_key: str | None = typer.Option(None, "--api-key", help="Override API key"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Debug logging"),
    config: str | None = typer.Option(None, "--config", help="Path to config file"),
) -> None:
    """Docmost CLI — manage your Docmost wiki from the terminal."""
    _ensure_utf8_stdio()
    cli_overrides: dict[str, str] = {}
    if url is not None:
        cli_overrides["url"] = url
    if api_key is not None:
        cli_overrides["api_key"] = api_key

    state.config_path = Path(config) if config else None
    state.settings = load_settings(
        profile=profile,
        config_path=state.config_path,
        cli_overrides=cli_overrides if cli_overrides else None,
    )
    state.verbose = verbose
    state.yes = yes


def get_client() -> DocmostClient:
    """Get or create the DocmostClient.

    Called by commands that need API access. Creates the client lazily
    so commands like 'config show' don't require a valid API connection.

    Returns:
        A configured DocmostClient instance.
    """
    if state.client is None:
        if state.settings is None:
            print_error("Not configured. Run 'docmost-cli config init'.", exit_code=1)
        state.client = DocmostClient(state.settings, verbose=state.verbose)
    return state.client


# Register subcommand groups
from docmost_cli.cli.config_cmd import config_app  # noqa: E402

app.add_typer(config_app)

from docmost_cli.cli.page import page_app  # noqa: E402

app.add_typer(page_app)

from docmost_cli.cli.space import space_app  # noqa: E402

app.add_typer(space_app)

from docmost_cli.cli.comment import comment_app  # noqa: E402

app.add_typer(comment_app)

from docmost_cli.cli.search import search_app  # noqa: E402

app.add_typer(search_app)

from docmost_cli.cli.attachment import attachment_app  # noqa: E402

app.add_typer(attachment_app)

from docmost_cli.cli.workspace import workspace_app  # noqa: E402

app.add_typer(workspace_app)

from docmost_cli.cli.user import user_app  # noqa: E402

app.add_typer(user_app)

from docmost_cli.cli.sync_cmd import sync_app  # noqa: E402

app.add_typer(sync_app)
