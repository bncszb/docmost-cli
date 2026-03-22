"""Workspace API methods."""

from typing import Any

from docmost_cli.api.client import DocmostClient

__all__ = [
    "get_workspace_info",
    "list_workspace_members",
]


def get_workspace_info(client: DocmostClient) -> dict[str, Any]:
    """Get workspace information.

    Args:
        client: Authenticated Docmost client.

    Returns:
        Raw API response dict with workspace details.
    """
    return client.post("/workspace/info", json={})


def list_workspace_members(
    client: DocmostClient,
    *,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """List workspace members with optional pagination.

    Args:
        client: Authenticated Docmost client.
        limit: Max results to return.
        cursor: Pagination cursor.

    Returns:
        Raw API response dict with members list.
    """
    body: dict[str, Any] = {}
    if limit is not None:
        body["limit"] = limit
    if cursor is not None:
        body["cursor"] = cursor
    return client.post("/workspace/members", json=body)
