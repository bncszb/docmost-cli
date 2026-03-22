"""Page subcommands."""

import json
import sys
from pathlib import Path

import typer

from docmost_cli.api.pages import (
    copy_page,
    create_page_via_import,
    delete_page,
    duplicate_page,
    export_page,
    get_page_children,
    get_page_content,
    get_page_history,
    get_page_info,
    get_sidebar_pages,
    import_page,
    list_recent_pages,
    move_page,
    update_page_content,
    update_page_meta,
)
from docmost_cli.api.pagination import extract_id, extract_items
from docmost_cli.api.spaces import resolve_space_id
from docmost_cli.cli.main import get_client, state
from docmost_cli.output.formatter import (
    print_content,
    print_content_with_meta,
    print_error,
    print_result,
    print_table,
)
from docmost_cli.output.tree import print_tree

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
        # Interpret common escape sequences so --content "Line 1\n\nLine 2" works
        return content.replace("\\n", "\n").replace("\\t", "\t")
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
    page_id = extract_id(result)

    # Import endpoint ignores parentPageId — move page as fallback
    if parent and page_id:
        move_page(client, page_id=page_id, parent_page_id=parent, position="aaaaa")

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
    position: str | None = typer.Option(None, "--position", help="Position among siblings"),
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


@page_app.command("list")
def page_list_cmd(
    space_slug: str = typer.Argument(help="Space slug to list pages in"),
    limit: int | None = typer.Option(None, "--limit", help="Max results (default: 50)"),
    cursor: str | None = typer.Option(None, "--cursor", help="Pagination cursor"),
    tree: bool = typer.Option(False, "--tree", help="Show as indented tree"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON array"),
) -> None:
    """List pages in a space."""
    client = get_client()
    space_id = resolve_space_id(client, space_slug)

    if tree:
        result = get_sidebar_pages(client, space_id)
        pages = extract_items(result)
        print_tree(pages)
        return

    result = list_recent_pages(client, space_id, limit=limit, cursor=cursor)
    items = extract_items(result)
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


@page_app.command("duplicate")
def page_duplicate_cmd(
    page_id: str = typer.Argument(help="Page ID to duplicate"),
) -> None:
    """Duplicate a page."""
    client = get_client()
    info = get_page_info(client, page_id)
    page_title = info.get("title", page_id)
    result = duplicate_page(client, page_id)
    new_id = extract_id(result)
    print_result(new_id, f"Duplicated page '{page_title}'")


@page_app.command("copy")
def page_copy_cmd(
    page_id: str = typer.Argument(help="Page ID to copy"),
    space: str = typer.Option(..., "--space", help="Target space slug (required)"),
) -> None:
    """Copy a page to a different space."""
    client = get_client()
    info = get_page_info(client, page_id)
    page_title = info.get("title", page_id)
    target_space_id = resolve_space_id(client, space)
    result = copy_page(client, page_id, target_space_id)
    new_id = extract_id(result)
    print_result(new_id, f"Copied page '{page_title}' to space '{space}'")


@page_app.command("children")
def page_children_cmd(
    page_id: str = typer.Argument(help="Page ID to list children for"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON array"),
) -> None:
    """List child pages."""
    client = get_client()
    result = get_page_children(client, page_id)
    items = extract_items(result)
    columns = ["id", "title", "icon", "updatedAt"]
    print_table(items, columns, json_mode=json_mode)


@page_app.command("history")
def page_history_cmd(
    page_id: str = typer.Argument(help="Page ID to show history for"),
    limit: int | None = typer.Option(None, "--limit", help="Max results"),
    json_mode: bool = typer.Option(False, "--json", help="Output as JSON array"),
) -> None:
    """Show page version history."""
    client = get_client()
    result = get_page_history(client, page_id, limit=limit)
    items = extract_items(result)
    columns = ["id", "creatorId", "createdAt"]
    print_table(items, columns, json_mode=json_mode)


@page_app.command("export")
def page_export_cmd(
    page_id: str = typer.Argument(help="Page ID to export"),
    fmt: str = typer.Option("md", "--format", help="Export format: md or html"),
    output: Path | None = typer.Option(None, "--output", help="Write to file instead of stdout"),
) -> None:
    """Export page content."""
    client = get_client()
    content = export_page(client, page_id, fmt=fmt)

    if output:
        if output.exists() and not state.yes:
            typer.confirm(f"File '{output}' already exists. Overwrite?", abort=True)
        output.write_text(str(content), encoding="utf-8")
        from rich.console import Console

        Console(stderr=True).print(f"Exported to {output}")
    else:
        print_content(str(content))


@page_app.command("import")
def page_import_cmd(
    space_slug: str = typer.Argument(help="Space slug to import into"),
    file: Path = typer.Option(..., "--file", help="Markdown or HTML file to import"),
    title: str | None = typer.Option(None, "--title", help="Override page title"),
    parent: str | None = typer.Option(None, "--parent", help="Parent page ID"),
) -> None:
    """Import a file as a new page."""
    if not file.exists():
        print_error(f"File not found: {file}")

    client = get_client()
    space_id = resolve_space_id(client, space_slug)

    # Read file once
    file_bytes = file.read_bytes()
    file_text = file_bytes.decode("utf-8", errors="replace")

    # Auto-detect title: flag > H1 in file > filename stem
    detected_title = title
    if not detected_title:
        for line in file_text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                detected_title = stripped[2:].strip()
                break
    if not detected_title:
        detected_title = file.stem

    result = import_page(
        client,
        space_id=space_id,
        file_name=file.name,
        file_bytes=file_bytes,
        parent_page_id=parent,
    )
    new_id = extract_id(result)
    print_result(new_id, f"Imported '{detected_title}' from {file.name}")
