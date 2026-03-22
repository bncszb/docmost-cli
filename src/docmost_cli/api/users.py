"""User API methods."""

from typing import Any

from docmost_cli.api.client import DocmostClient

__all__ = [
    "get_current_user",
]


def get_current_user(client: DocmostClient) -> dict[str, Any]:
    """Get the currently authenticated user's info.

    Args:
        client: Authenticated Docmost client.

    Returns:
        Raw API response dict with user details.
    """
    return client.post("/users/me", json={})
