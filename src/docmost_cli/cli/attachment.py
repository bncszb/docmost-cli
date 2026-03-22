"""Attachment subcommands."""

from typing import Any

import typer

from docmost_cli.api.attachments import search_attachments
from docmost_cli.api.spaces import resolve_space_id
from docmost_cli.cli.main import get_client
from docmost_cli.output.formatter import print_table

__all__ = ["attachment_app"]

attachment_app = typer.Typer(name="attachment", help="Attachment operations.")


def _extract_items(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract items list from API response, handling nested shapes."""
    if "data" in response and isinstance(response["data"], dict):
        return response["data"].get("items", [])
    if "data" in response and isinstance(response["data"], list):
        return response["data"]
    return response.get("items", [response] if "id" in response else [])


@attachment_app.command("search")
def attachment_search_cmd(
    query: str = typer.Argument(..., help="Search query string"),
    space: str | None = typer.Option(None, "--space", help="Space slug to scope search"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON array"),
) -> None:
    """Search attachments."""
    client = get_client()
    space_id = None
    if space:
        space_id = resolve_space_id(client, space)
    result = search_attachments(client, query, space_id=space_id)
    items = _extract_items(result)
    columns = ["id", "fileName", "type"]
    print_table(items, columns, json_mode=json_mode)
