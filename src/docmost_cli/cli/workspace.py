"""Workspace subcommands."""

import typer

__all__ = ["workspace_app"]

workspace_app = typer.Typer(name="workspace", help="Workspace info.")
