"""Page API methods."""

from typing import Any

from docmost_cli.api.client import DocmostClient
from docmost_cli.api.pagination import build_body
from docmost_cli.output.formatter import print_error

__all__ = [
    "copy_page",
    "create_page_via_import",
    "delete_page",
    "duplicate_page",
    "export_page",
    "get_page_children",
    "get_page_content",
    "get_page_history",
    "get_page_info",
    "get_sidebar_pages",
    "import_page",
    "list_recent_pages",
    "move_page",
    "update_page_content",
    "update_page_meta",
]


def get_page_info(client: DocmostClient, page_id: str) -> dict[str, Any]:
    """Get page metadata by ID.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID.

    Returns:
        Page info dict (unwrapped from data envelope).
    """
    result = client.post("/pages/info", json={"pageId": page_id})
    return result.get("data", result)


def create_page_via_import(
    client: DocmostClient,
    *,
    space_id: str,
    title: str,
    content: str,
    parent_page_id: str | None = None,
) -> dict[str, Any]:
    """Create a page using the import endpoint (server-side MD→ProseMirror).

    Sends Markdown as a .md file via multipart upload. Available on both
    Community and Enterprise editions.

    Args:
        client: Authenticated Docmost client.
        space_id: Target space UUID.
        title: Page title.
        content: Markdown content.
        parent_page_id: Parent page UUID (optional).

    Returns:
        Raw API response dict (should contain page ID).
    """
    # Ensure content has the title as H1 if not already present
    md_content = content
    if md_content and not md_content.lstrip().startswith("#"):
        md_content = f"# {title}\n\n{md_content}"
    elif not md_content:
        md_content = f"# {title}\n"

    file_bytes = md_content.encode("utf-8")
    files = {"file": (f"{title}.md", file_bytes, "text/markdown")}
    data: dict[str, str] = {"spaceId": space_id}
    if parent_page_id:
        data["parentPageId"] = parent_page_id

    return client.post_multipart("/pages/import", data=data, files=files)


def update_page_meta(
    client: DocmostClient,
    *,
    page_id: str,
    title: str | None = None,
    icon: str | None = None,
) -> dict[str, Any]:
    """Update page metadata (title, icon).

    Available on both Community and Enterprise editions.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID.
        title: New title.
        icon: New icon emoji.

    Returns:
        Raw API response dict.
    """
    body = build_body({"pageId": page_id}, title=title, icon=icon)
    return client.post("/pages/update", json=body)


def update_page_content(
    client: DocmostClient,
    *,
    page_id: str,
    content: str,
    fmt: str = "markdown",
) -> dict[str, Any]:
    """Update page content via REST endpoint.

    This endpoint may only be available on Enterprise edition (v0.70+).
    On Community edition, this may return 404/405.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID.
        content: Markdown or HTML content.
        fmt: Content format ("markdown" or "html").

    Returns:
        Raw API response dict.
    """
    try:
        return client.post(
            "/pages/content/update",
            json={"pageId": page_id, "content": content, "format": fmt},
        )
    except SystemExit as exc:
        if exc.code == 4:  # 404 — endpoint not available
            print_error(
                "Content update is not available on this Docmost instance. "
                "This feature may require Enterprise edition (v0.70+). "
                "Use 'docmost-cli page delete' + 'docmost-cli page create' "
                "to replace page content.",
                exit_code=1,
            )
        raise


def delete_page(client: DocmostClient, page_id: str) -> dict[str, Any]:
    """Delete a page by ID.

    Available on both Community and Enterprise editions.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID.

    Returns:
        Raw API response dict.
    """
    return client.post("/pages/delete", json={"pageId": page_id})


def move_page(
    client: DocmostClient,
    *,
    page_id: str,
    parent_page_id: str | None = None,
    space_id: str | None = None,
    position: str | int | None = None,
) -> dict[str, Any]:
    """Move a page to a new location.

    Available on both Community and Enterprise editions.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID.
        parent_page_id: New parent page UUID (omit for root).
        space_id: Target space UUID (for cross-space moves).
        position: Position among siblings (fractional index string, 5-12 chars).

    Returns:
        Raw API response dict.
    """
    body = build_body(
        {"pageId": page_id},
        parentPageId=parent_page_id,
        spaceId=space_id,
        position=position,
    )
    return client.post("/pages/move", json=body)


def get_page_content(client: DocmostClient, page_id: str) -> dict[str, Any]:
    """Get page content and metadata.

    Tries POST /pages/content (Enterprise v0.70+) first, then falls back
    to POST /pages/info which may include content on both editions.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID.

    Returns:
        Dict with page metadata and content (ProseMirror JSON).
    """
    # Try Enterprise content endpoint (silently — may not exist on Community)
    response = client.post_raw(
        "/pages/content", json={"pageId": page_id}, raise_on_error=False
    )
    if response.is_success:
        try:
            content_data = response.json()
            info = get_page_info(client, page_id)
            data = content_data.get("data", content_data)
            info["content"] = data.get("content", data)
            return info
        except (ValueError, KeyError):
            pass

    # Fall back to /pages/info (may include content on both editions)
    info = get_page_info(client, page_id)
    if "content" in info and info["content"]:
        return info

    print_error(
        "Page content not available via REST on this instance. "
        "This may require Enterprise edition (v0.70+). "
        "Try 'docmost-cli page get <id> --raw' or access the page in the web UI.",
        exit_code=1,
    )


def list_recent_pages(
    client: DocmostClient,
    space_id: str,
    *,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """List recent pages in a space with cursor-based pagination.

    Args:
        client: Authenticated Docmost client.
        space_id: Space UUID.
        limit: Max results to return.
        cursor: Pagination cursor.

    Returns:
        Raw API response dict.
    """
    body = build_body({"spaceId": space_id}, limit=limit, cursor=cursor)
    return client.post("/pages/recent", json=body)


def duplicate_page(client: DocmostClient, page_id: str) -> dict[str, Any]:
    """Duplicate a page.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID to duplicate.

    Returns:
        Raw API response dict (should contain new page ID).
    """
    return client.post("/pages/duplicate", json={"pageId": page_id})


def copy_page(
    client: DocmostClient, page_id: str, space_id: str
) -> dict[str, Any]:
    """Copy a page to a different space.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID to copy.
        space_id: Target space UUID.

    Returns:
        Raw API response dict (should contain new page ID).
    """
    return client.post("/pages/copy", json={"pageId": page_id, "spaceId": space_id})


def get_page_children(
    client: DocmostClient,
    page_id: str,
    *,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """List direct child pages.

    Args:
        client: Authenticated Docmost client.
        page_id: Parent page UUID.
        limit: Max results.
        cursor: Pagination cursor.

    Returns:
        Raw API response dict.
    """
    body = build_body({"pageId": page_id}, limit=limit, cursor=cursor)
    return client.post("/pages/children", json=body)


def get_page_history(
    client: DocmostClient,
    page_id: str,
    *,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Get page version history.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID.
        limit: Max results.
        cursor: Pagination cursor.

    Returns:
        Raw API response dict.
    """
    body = build_body({"pageId": page_id}, limit=limit, cursor=cursor)
    return client.post("/pages/history", json=body)


def export_page(
    client: DocmostClient, page_id: str, fmt: str = "md"
) -> str:
    """Export page content.

    Docmost returns a ZIP file containing the exported content.
    This function extracts the content from the ZIP.

    Args:
        client: Authenticated Docmost client.
        page_id: Page UUID.
        fmt: Export format ("md" or "html"). Accepts "md" as alias for "markdown".

    Returns:
        Exported content as a string.
    """
    import io
    import zipfile

    # Docmost expects "markdown" not "md"
    api_format = "markdown" if fmt == "md" else fmt
    response = client.post_raw("/pages/export", json={"pageId": page_id, "format": api_format})

    # Response is a ZIP file — extract content from it
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        names = zf.namelist()
        if not names:
            print_error("Export ZIP is empty.", exit_code=1)
        return zf.read(names[0]).decode("utf-8")


def get_sidebar_pages(client: DocmostClient, space_id: str) -> dict[str, Any]:
    """Get page tree structure for a space.

    Returns nested structure with children arrays, used for --tree view.

    Args:
        client: Authenticated Docmost client.
        space_id: Space UUID.

    Returns:
        Raw API response dict with nested page tree.
    """
    return client.post("/pages/sidebar-pages", json={"spaceId": space_id})


def import_page(
    client: DocmostClient,
    *,
    space_id: str,
    file_name: str,
    file_bytes: bytes,
    parent_page_id: str | None = None,
) -> dict[str, Any]:
    """Import a file as a new page via multipart upload.

    Args:
        client: Authenticated Docmost client.
        space_id: Target space UUID.
        file_name: Original filename (used for MIME detection and upload).
        file_bytes: Raw file content bytes.
        parent_page_id: Parent page UUID (optional).

    Returns:
        Raw API response dict (should contain new page ID).
    """
    mime = "text/html" if file_name.lower().endswith((".html", ".htm")) else "text/markdown"
    files = {"file": (file_name, file_bytes, mime)}
    data = build_body({"spaceId": space_id}, parentPageId=parent_page_id)
    return client.post_multipart("/pages/import", data=data, files=files)
