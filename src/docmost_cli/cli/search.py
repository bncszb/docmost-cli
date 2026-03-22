"""Search subcommand."""

import typer

__all__ = ["search_app"]

search_app = typer.Typer(name="search", help="Search across the wiki.")
