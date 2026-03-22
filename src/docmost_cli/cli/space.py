"""Space subcommands."""

import typer

from docmost_cli.api.pagination import extract_id, extract_items
from docmost_cli.api.spaces import (
    create_space,
    list_spaces,
    resolve_space_id,
    update_space,
)
from docmost_cli.cli.main import get_client
from docmost_cli.output.formatter import print_error, print_result, print_table

__all__ = ["space_app"]

space_app = typer.Typer(name="space", help="Space operations.")


@space_app.command("list")
def space_list_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON array"),
) -> None:
    """List all spaces."""
    client = get_client()
    result = list_spaces(client)
    items = extract_items(result)
    columns = ["id", "name", "slug", "description"]
    print_table(items, columns, json_mode=json_mode)


@space_app.command("create")
def space_create_cmd(
    name: str = typer.Option(..., "--name", help="Space name (required)"),
    slug: str | None = typer.Option(None, "--slug", help="Space slug (auto-generated if omitted)"),
    description: str | None = typer.Option(
        None, "--description", help="Space description"
    ),
) -> None:
    """Create a new space."""
    client = get_client()
    result = create_space(client, name=name, slug=slug, description=description)
    space_id = extract_id(result)
    print_result(space_id, f"Created space '{name}'")


@space_app.command("update")
def space_update_cmd(
    space_slug: str = typer.Argument(help="Space slug to update"),
    name: str | None = typer.Option(None, "--name", help="New space name"),
    description: str | None = typer.Option(None, "--description", help="New description"),
) -> None:
    """Update an existing space."""
    if name is None and description is None:
        print_error("At least one of --name or --description is required.")
    client = get_client()
    space_id = resolve_space_id(client, space_slug)
    update_space(client, space_id=space_id, name=name, description=description)
    print_result(space_id, f"Updated space '{space_slug}'")
