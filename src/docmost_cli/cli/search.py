"""Search subcommand."""

import typer

from docmost_cli.api.search import search
from docmost_cli.api.spaces import resolve_space_id
from docmost_cli.cli.main import get_client
from docmost_cli.output.formatter import print_table

__all__ = ["search_app"]

search_app = typer.Typer(name="search", help="Search across the wiki.")


def _extract_items(response: dict) -> list[dict]:
    """Extract items list from API response, handling nested shapes."""
    if "data" in response and isinstance(response["data"], dict):
        return response["data"].get("items", [])
    if "data" in response and isinstance(response["data"], list):
        return response["data"]
    return response.get("items", [response] if "id" in response else [])


@search_app.command("query")
def search_cmd(
    query: str = typer.Argument(help="Search query"),
    space: str | None = typer.Option(None, "--space", help="Filter by space slug"),
    limit: int | None = typer.Option(None, "--limit", help="Max results (default: 20)"),
    type_filter: str | None = typer.Option(None, "--type", help="Filter: page or attachment"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON array"),
) -> None:
    """Full-text search across the wiki."""
    client = get_client()
    space_id = None
    if space is not None:
        space_id = resolve_space_id(client, space)

    result = search(client, query, space_id=space_id, result_type=type_filter, limit=limit)
    items = _extract_items(result)
    columns = ["id", "title", "highlight"]
    print_table(items, columns, json_mode=json_mode)
