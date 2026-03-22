"""Workspace subcommands."""

from typing import Any

import typer

from docmost_cli.api.pagination import extract_items
from docmost_cli.api.workspace import get_workspace_info, list_workspace_members
from docmost_cli.cli.main import get_client
from docmost_cli.output.formatter import print_key_value, print_table

__all__ = ["workspace_app"]

workspace_app = typer.Typer(name="workspace", help="Workspace info.")


@workspace_app.command("info")
def workspace_info_cmd() -> None:
    """Show workspace details."""
    client = get_client()
    result = get_workspace_info(client)
    data = result.get("data", result)
    display: dict[str, Any] = {}
    for key in ["name", "id", "description", "memberCount", "createdAt"]:
        if key in data:
            display[key] = data[key]
    print_key_value(display)


@workspace_app.command("members")
def workspace_members_cmd(
    limit: int | None = typer.Option(None, "--limit", help="Max results"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON array"),
) -> None:
    """List workspace members."""
    client = get_client()
    result = list_workspace_members(client, limit=limit)
    items = extract_items(result)
    columns = ["id", "email", "name", "role"]
    print_table(items, columns, json_mode=json_mode)
