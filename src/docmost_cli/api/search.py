"""Search API methods."""

from typing import Any

from docmost_cli.api.client import DocmostClient

__all__ = ["search"]


def search(
    client: DocmostClient,
    query: str,
    *,
    space_id: str | None = None,
    result_type: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """Full-text search across the wiki.

    Args:
        client: Authenticated Docmost client.
        query: Search query string.
        space_id: Optional space UUID to filter results.
        result_type: Optional type filter ("page" or "attachment").
        limit: Max results (default server-side, typically 20).
        cursor: Pagination cursor.

    Returns:
        Raw API response dict.
    """
    body: dict[str, Any] = {"query": query}
    if space_id is not None:
        body["spaceId"] = space_id
    if result_type is not None:
        body["type"] = result_type
    if limit is not None:
        body["limit"] = limit
    if cursor is not None:
        body["cursor"] = cursor
    return client.post("/search", json=body)
