"""Shared data models used across the project."""

from pydantic import BaseModel

__all__ = ["PaginatedRequest", "PaginatedResponse", "AuthTokens"]


class PaginatedRequest(BaseModel):
    """Base for requests that support cursor-based pagination."""

    limit: int | None = None
    cursor: str | None = None


class PaginatedResponse(BaseModel):
    """Wraps the standard Docmost paginated response shape."""

    items: list[dict] = []
    cursor: str | None = None


class AuthTokens(BaseModel):
    """Cached session authentication tokens."""

    token: str
    url: str
    email: str
    created_at: str
