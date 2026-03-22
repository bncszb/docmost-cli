"""Authentication strategies for Docmost API.

Supports two auth modes:
- API key (Enterprise): Bearer token in Authorization header
- Session (Community/AGPL): POST /api/auth/login, cache JWT
"""

import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

import httpx

from docmost_cli.config.settings import DocmostSettings
from docmost_cli.config.store import get_cache_dir

__all__ = ["ApiKeyAuth", "AuthError", "AuthStrategy", "SessionAuth", "create_auth"]


class AuthError(Exception):
    """Raised when authentication fails."""


class AuthStrategy(ABC):
    """Base class for authentication strategies."""

    @abstractmethod
    def apply(self, request: httpx.Request) -> None:
        """Add auth headers to a request."""

    @abstractmethod
    def can_retry(self) -> bool:
        """Whether this strategy supports re-authentication on 401."""

    @abstractmethod
    def refresh(self, client: httpx.Client) -> None:
        """Re-authenticate. Called on 401 if can_retry() is True."""


class ApiKeyAuth(AuthStrategy):
    """Bearer token authentication for Enterprise edition."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def apply(self, request: httpx.Request) -> None:
        """Set Authorization: Bearer header."""
        request.headers["Authorization"] = f"Bearer {self._api_key}"

    def can_retry(self) -> bool:
        """API key is static; no retry possible."""
        return False

    def refresh(self, client: httpx.Client) -> None:
        """Not supported for API key auth."""
        raise AuthError("API key authentication failed. Check your API key.")


class SessionAuth(AuthStrategy):
    """Session-based authentication for Community/AGPL edition.

    Authenticates via POST /api/auth/login, extracts JWT from the response,
    and caches it in ~/.cache/docmost-cli/session.json.
    """

    def __init__(self, url: str, email: str, password: str) -> None:
        self._url = url.rstrip("/")
        self._email = email
        self._password = password
        self._token: str | None = None
        self._load_cached_token()

    def _cache_path(self) -> Path:
        """Return the path to the session cache file."""
        return get_cache_dir() / "session.json"

    def _load_cached_token(self) -> None:
        """Try to load a cached JWT from the cache file."""
        cache = self._cache_path()
        if not cache.exists():
            return
        try:
            data = json.loads(cache.read_text())
            if data.get("url") == self._url and data.get("email") == self._email:
                self._token = data.get("token")
        except (json.JSONDecodeError, KeyError):
            pass

    def _save_cached_token(self) -> None:
        """Save the current JWT to the cache file."""
        if not self._token:
            return
        cache = self._cache_path()
        cache.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "token": self._token,
            "url": self._url,
            "email": self._email,
            "created_at": datetime.now(UTC).isoformat(),
        }
        cache.write_text(json.dumps(data, indent=2))

    def apply(self, request: httpx.Request) -> None:
        """Set Authorization header from cached token."""
        if self._token:
            request.headers["Authorization"] = f"Bearer {self._token}"

    def can_retry(self) -> bool:
        """Session auth supports re-authentication."""
        return True

    def refresh(self, client: httpx.Client) -> None:
        """POST /api/auth/login to get a fresh JWT.

        Extracts the token from the response JSON body or Set-Cookie header.

        Args:
            client: The httpx client to use for the login request.

        Raises:
            AuthError: If login fails.
        """
        login_url = f"{self._url}/api/auth/login"
        try:
            response = client.post(
                login_url,
                json={"email": self._email, "password": self._password},
            )
        except httpx.HTTPError as exc:
            raise AuthError(f"Failed to connect for authentication: {exc}") from exc

        if response.status_code != 200:
            raise AuthError(
                f"Authentication failed (HTTP {response.status_code}). "
                "Check your email and password."
            )

        # Try to extract token from response JSON
        try:
            body = response.json()
            token = body.get("token")
        except (json.JSONDecodeError, AttributeError):
            token = None

        # Fallback: try Set-Cookie header
        if not token:
            for cookie_header in response.headers.get_list("set-cookie"):
                if "token=" in cookie_header:
                    token = cookie_header.split("token=")[1].split(";")[0]
                    break

        if not token:
            raise AuthError(
                "Authentication succeeded but no token found in response. "
                "This may be an unsupported Docmost version."
            )

        self._token = token
        self._save_cached_token()


def create_auth(settings: DocmostSettings) -> AuthStrategy:
    """Create the appropriate auth strategy based on settings.

    Priority: api_key > email+password > error.

    Args:
        settings: The resolved settings.

    Returns:
        An AuthStrategy instance.

    Raises:
        AuthError: If no credentials are configured.
    """
    if settings.api_key:
        return ApiKeyAuth(settings.api_key)

    if settings.email and settings.password:
        if not settings.url:
            raise AuthError("URL is required for session authentication.")
        return SessionAuth(settings.url, settings.email, settings.password)

    raise AuthError(
        "No authentication configured. "
        "Set DOCMOST_API_KEY or DOCMOST_EMAIL + DOCMOST_PASSWORD. "
        "Run 'docmost-cli config init' for interactive setup."
    )
