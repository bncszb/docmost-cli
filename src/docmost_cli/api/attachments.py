"""Attachment API methods."""

from typing import Any

from docmost_cli.api.client import DocmostClient

__all__ = [
    "search_attachments",
]


def search_attachments(
    client: DocmostClient,
    query: str,
    *,
    space_id: str | None = None,
) -> dict[str, Any]:
    """Search attachments by query string.

    Args:
        client: Authenticated Docmost client.
        query: Search query string.
        space_id: Optional space UUID to scope the search.

    Returns:
        Raw API response dict with matching attachments.
    """
    body: dict[str, Any] = {"query": query}
    if space_id is not None:
        body["spaceId"] = space_id
    return client.post("/attachments/search", json=body)
