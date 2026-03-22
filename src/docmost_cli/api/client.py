"""DocmostClient: central HTTP client with auth, retry, and error handling.

All API calls go through this client. It handles:
- Auth header injection via AuthStrategy
- 401 retry (session auth re-authentication)
- HTTP error translation to user-friendly messages with exit codes
"""

from typing import Any

import httpx

from docmost_cli.api.auth import AuthError, AuthStrategy, create_auth
from docmost_cli.config.settings import DocmostSettings
from docmost_cli.output.formatter import print_error

__all__ = ["DocmostClient"]


class DocmostClient:
    """HTTP client for the Docmost API.

    Uses httpx.Client for connection pooling. Provides authenticated
    request methods with automatic error handling.
    """

    def __init__(self, settings: DocmostSettings) -> None:
        if not settings.url:
            print_error(
                "No Docmost URL configured. "
                "Run 'docmost-cli config init' or set DOCMOST_URL.",
                exit_code=1,
            )

        self._settings = settings
        self._base_url = settings.url.rstrip("/")  # type: ignore[union-attr]
        self._auth: AuthStrategy = create_auth(settings)
        self._http = httpx.Client(timeout=30.0)

    def _send_with_retry(self, request: httpx.Request) -> httpx.Response:
        """Send a request with auth injection, 401 retry, and error handling.

        Args:
            request: The prepared httpx request.

        Returns:
            The HTTP response (success only; errors raise SystemExit).
        """
        self._auth.apply(request)

        try:
            response = self._http.send(request)
        except httpx.ConnectError:
            print_error(
                f"Cannot connect to {self._base_url}. Check the URL and your network.",
                exit_code=1,
            )
        except httpx.TimeoutException:
            print_error(
                f"Request timed out connecting to {self._base_url}.",
                exit_code=1,
            )

        # Handle 401 retry for session auth
        if response.status_code == 401 and self._auth.can_retry():
            try:
                self._auth.refresh(self._http)
            except AuthError as exc:
                print_error(str(exc), exit_code=3)

            # Rebuild request for retry (cannot reuse consumed request)
            request = self._http.build_request(
                request.method,
                str(request.url),
                headers=dict(request.headers),
                content=request.content,
            )
            self._auth.apply(request)
            try:
                response = self._http.send(request)
            except httpx.HTTPError:
                print_error("Request failed after re-authentication.", exit_code=1)

        # Translate HTTP errors
        self._handle_error(response)

        return response

    def request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make an authenticated API request with error handling.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API path relative to /api/ (e.g., "/pages/info").
            **kwargs: Additional arguments passed to httpx (json, params, etc.).

        Returns:
            Parsed JSON response body.
        """
        url = f"{self._base_url}/api{path}"
        request = self._http.build_request(method, url, **kwargs)
        response = self._send_with_retry(request)
        return response.json()

    def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Convenience method for POST requests.

        Most Docmost API endpoints use POST.

        Args:
            path: API path relative to /api/.
            json: JSON body to send.

        Returns:
            Parsed JSON response body.
        """
        return self.request("POST", path, json=json)

    def post_multipart(
        self,
        path: str,
        data: dict[str, str] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """POST with multipart/form-data for file uploads.

        Args:
            path: API path relative to /api/.
            data: Form fields.
            files: File fields (httpx files format).

        Returns:
            Parsed JSON response body.
        """
        url = f"{self._base_url}/api{path}"
        request = self._http.build_request("POST", url, data=data, files=files)
        response = self._send_with_retry(request)
        return response.json()

    def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Convenience method for GET requests.

        Args:
            path: API path relative to /api/.
            **kwargs: Additional arguments (params, etc.).

        Returns:
            Parsed JSON response body.
        """
        return self.request("GET", path, **kwargs)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> "DocmostClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    @staticmethod
    def _handle_error(response: httpx.Response) -> None:
        """Translate HTTP error responses to user-friendly messages.

        Args:
            response: The HTTP response to check.
        """
        if response.is_success:
            return

        status = response.status_code

        if status == 401:
            print_error(
                "Authentication failed. Run 'docmost-cli config test' to verify.",
                exit_code=3,
            )
        elif status == 403:
            print_error("Permission denied.", exit_code=1)
        elif status == 404:
            print_error(
                "Resource not found. Check the ID or slug.",
                exit_code=4,
            )
        elif status == 422:
            try:
                detail = response.json().get("message", "Validation error")
            except Exception:
                detail = "Validation error"
            print_error(f"Validation error: {detail}", exit_code=1)
        elif status == 429:
            print_error("Rate limited. Try again later.", exit_code=1)
        elif status >= 500:
            print_error(
                f"Server error ({status}). Check Docmost logs.",
                exit_code=1,
            )
        else:
            print_error(
                f"Unexpected error (HTTP {status}).",
                exit_code=1,
            )
