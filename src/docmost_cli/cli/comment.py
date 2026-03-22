"""Comment subcommands."""

import typer

__all__ = ["comment_app"]

comment_app = typer.Typer(name="comment", help="Comment operations.")
