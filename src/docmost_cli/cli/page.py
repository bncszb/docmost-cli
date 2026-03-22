"""Page subcommands."""

import json
import sys
from pathlib import Path

import typer

from docmost_cli.api.pages import (
    create_page_via_import,
    delete_page,
    get_page_content,
    get_page_info,
    list_recent_pages,
    move_page,
    update_page_content,
    update_page_meta,
)
from docmost_cli.api.spaces import resolve_space_id
from docmost_cli.cli.main import get_client, state
from docmost_cli.output.formatter import (
    print_content,
    print_content_with_meta,
    print_error,
    print_result,
    print_table,
)

__all__ = ["page_app"]

page_app = typer.Typer(name="page", help="Page operations.")


def _resolve_content(
    content: str | None,
    file: Path | None,
    stdin: bool,
) -> str | None:
    """Resolve content from --content, --file, or --stdin.

    These are mutually exclusive. Returns None if no source provided.

    Args:
        content: Inline content string.
        file: Path to content file.
        stdin: Whether to read from stdin.

    Returns:
        Resolved content string, or None.
    """
    sources = sum([content is not None, file is not None, stdin])
    if sources > 1:
        print_error("Only one of --content, --file, or --stdin may be specified.")
    if sources == 0:
        return None
    if content is not None:
        return content
    if file is not None:
        if not file.exists():
            print_error(f"File not found: {file}")
        return file.read_text(encoding="utf-8")
    # stdin
    if sys.stdin.isatty():
        print_error(
            "No input piped to stdin. "
            "Use --content or --file instead, or pipe input: "
            "echo '# Page' | docmost-cli page create ..."
        )
    return sys.stdin.read()


@page_app.command("create")
def page_create_cmd(
    space_slug: str = typer.Argument(help="Space slug to create the page in"),
    title: str = typer.Option(..., "--title", help="Page title (required)"),
    content: str | None = typer.Option(None, "--content", help="Markdown content string"),
    file: Path | None = typer.Option(None, "--file", help="Read content from file"),
    stdin: bool = typer.Option(False, "--stdin", help="Read content from stdin"),
    parent: str | None = typer.Option(None, "--parent", help="Parent page ID"),
    icon: str | None = typer.Option(None, "--icon", help="Page icon emoji"),
) -> None:
    """Create a new page via Markdown import."""
    resolved = _resolve_content(content, file, stdin) or ""
    client = get_client()
    space_id = resolve_space_id(client, space_slug)

    result = create_page_via_import(
        client,
        space_id=space_id,
        title=title,
        content=resolved,
        parent_page_id=parent,
    )
    page_id = result.get("id") or result.get("data", {}).get("id", "")

    # Set icon separately if provided (import endpoint may not support it)
    if icon and page_id:
        update_page_meta(client, page_id=page_id, icon=icon)

    msg = f"Created page '{title}' in space '{space_slug}'"
    if not resolved:
        msg = f"Created empty page '{title}' in space '{space_slug}'"
    print_result(page_id, msg)


@page_app.command("update")
def page_update_cmd(
    page_id: str = typer.Argument(help="Page ID to update"),
    title: str | None = typer.Option(None, "--title", help="New title"),
    content: str | None = typer.Option(None, "--content", help="New content (Markdown)"),
    file: Path | None = typer.Option(None, "--file", help="Read content from file"),
    stdin: bool = typer.Option(False, "--stdin", help="Read content from stdin"),
) -> None:
    """Update an existing page's title and/or content."""
    resolved = _resolve_content(content, file, stdin)
    if title is None and resolved is None:
        print_error(
            "At least one of --title, --content, --file, or --stdin is required."
        )

    client = get_client()
    info = get_page_info(client, page_id)
    page_title = info.get("title", page_id)

    if title is not None:
        update_page_meta(client, page_id=page_id, title=title)
        page_title = title

    if resolved is not None:
        update_page_content(client, page_id=page_id, content=resolved)

    print_result(page_id, f"Updated page '{page_title}'")


@page_app.command("delete")
def page_delete_cmd(
    page_id: str = typer.Argument(help="Page ID to delete"),
) -> None:
    """Delete a page (requires confirmation unless --yes)."""
    client = get_client()
    info = get_page_info(client, page_id)
    page_title = info.get("title", page_id)

    if not state.yes:
        typer.confirm(f"Delete page '{page_title}' ({page_id})?", abort=True)

    delete_page(client, page_id)
    print_result(page_id, f"Deleted page '{page_title}'")


@page_app.command("move")
def page_move_cmd(
    page_id: str = typer.Argument(help="Page ID to move"),
    parent: str | None = typer.Option(None, "--parent", help="New parent page ID"),
    space: str | None = typer.Option(None, "--space", help="Target space slug"),
    position: int | None = typer.Option(None, "--position", help="Position among siblings"),
) -> None:
    """Move a page to a new location."""
    if parent is None and space is None and position is None:
        print_error("At least one of --parent, --space, or --position is required.")

    client = get_client()
    target_space_id = None
    if space is not None:
        target_space_id = resolve_space_id(client, space)

    move_page(
        client,
        page_id=page_id,
        parent_page_id=parent,
        space_id=target_space_id,
        position=position,
    )
    print_result(page_id, f"Moved page '{page_id}'")


def _extract_items(response: dict) -> list[dict]:
    """Extract items list from API response, handling nested shapes."""
    if "data" in response and isinstance(response["data"], dict):
        return response["data"].get("items", [])
    if "data" in response and isinstance(response["data"], list):
        return response["data"]
    return response.get("items", [response] if "id" in response else [])


@page_app.command("list")
def page_list_cmd(
    space_slug: str = typer.Argument(help="Space slug to list pages in"),
    limit: int | None = typer.Option(None, "--limit", help="Max results (default: 50)"),
    cursor: str | None = typer.Option(None, "--cursor", help="Pagination cursor"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON array"),
) -> None:
    """List pages in a space."""
    client = get_client()
    space_id = resolve_space_id(client, space_slug)
    result = list_recent_pages(client, space_id, limit=limit, cursor=cursor)
    items = _extract_items(result)
    columns = ["id", "title", "icon", "updatedAt"]
    print_table(items, columns, json_mode=json_mode)


@page_app.command("get")
def page_get_cmd(
    page_id: str = typer.Argument(help="Page ID to retrieve"),
    raw: bool = typer.Option(False, "--raw", help="Output ProseMirror JSON instead of Markdown"),
    meta: bool = typer.Option(False, "--meta", help="Prepend YAML frontmatter with metadata"),
) -> None:
    """Get page content as Markdown."""
    client = get_client()

    if raw:
        # Raw mode: try content endpoint, fall back to info
        try:
            data = client.post("/pages/content", json={"pageId": page_id})
            pm_content = data.get("content", data)
        except SystemExit:
            info = get_page_info(client, page_id)
            pm_content = info.get("content")
            if not pm_content:
                print_error("No content available for raw output.", exit_code=1)
        sys.stdout.write(json.dumps(pm_content, indent=2) + "\n")
        return

    # Normal mode: get content and convert to Markdown
    info = get_page_content(client, page_id)
    pm_content = info.get("content")
    if not pm_content:
        print_error("Page has no content.", exit_code=1)

    from docmost_cli.convert.prosemirror_to_md import convert_to_markdown

    markdown = convert_to_markdown(pm_content)

    if meta:
        metadata = {
            "id": info.get("id", ""),
            "title": info.get("title", ""),
            "space_id": info.get("spaceId", ""),
            "created": info.get("createdAt", ""),
            "updated": info.get("updatedAt", ""),
        }
        print_content_with_meta(markdown, metadata)
    else:
        print_content(markdown)
