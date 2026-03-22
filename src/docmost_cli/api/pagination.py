"""Pagination utilities for cursor-based API responses.

Provides shared helpers for extracting items from varying response shapes
and auto-following pagination cursors.
"""

from collections.abc import Callable
from typing import Any

__all__ = ["extract_items", "get_cursor", "paginate_all"]


def extract_items(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract items list from API response, handling nested shapes.

    Handles: {data: {items: [...]}}, {data: [...]}, {items: [...]}, and flat dicts.

    Args:
        response: Raw API response dict.

    Returns:
        List of item dicts.
    """
    if "data" in response and isinstance(response["data"], dict):
        return response["data"].get("items", [])
    if "data" in response and isinstance(response["data"], list):
        return response["data"]
    return response.get("items", [response] if "id" in response else [])


def get_cursor(response: dict[str, Any]) -> str | None:
    """Extract pagination cursor from API response.

    Args:
        response: Raw API response dict.

    Returns:
        Next cursor string, or None if no more pages.
    """
    if "data" in response and isinstance(response["data"], dict):
        return response["data"].get("cursor")
    return response.get("cursor")


def paginate_all(
    fetch_func: Callable[..., dict[str, Any]],
    *,
    limit: int | None = None,
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Auto-follow pagination until exhausted or limit reached.

    Calls fetch_func repeatedly with cursor parameter until no more
    pages are available or the total item count reaches limit.

    Args:
        fetch_func: API function that accepts cursor= keyword arg.
        limit: Max total items to collect (None = all).
        **kwargs: Additional arguments passed to fetch_func.

    Returns:
        Combined list of all items across pages.
    """
    max_iterations = 1000  # Safety guard against infinite loops
    all_items: list[dict[str, Any]] = []
    cursor: str | None = None

    for _ in range(max_iterations):
        response = fetch_func(**kwargs, cursor=cursor)
        items = extract_items(response)
        all_items.extend(items)

        if limit and len(all_items) >= limit:
            return all_items[:limit]

        cursor = get_cursor(response)
        if not cursor:
            break

    return all_items
