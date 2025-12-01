"""Lightweight HTTP client for the Dari public API."""
from __future__ import annotations

from typing import Any, Dict, Mapping, MutableMapping, Optional

import requests
from requests import Response, Session

from ._version import __version__

DEFAULT_BASE_URL = "https://api.usedari.com"
DEFAULT_TIMEOUT = 30  # seconds


class DariError(Exception):
    """Raised when the Dari API returns an error or the request fails."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, response: Optional[Response] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class Dari:
    """Tiny convenience wrapper around the Dari REST API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int | float = DEFAULT_TIMEOUT,
        session: Optional[Session] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must be provided")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        self._default_headers: Dict[str, str] = {
            "X-API-Key": api_key,
            "User-Agent": f"dari-python/{__version__}",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Workflow execution helpers
    # ------------------------------------------------------------------
    def start_workflow(
        self,
        workflow_id: str,
        input_variables: Mapping[str, Any],
        *,
        timeout_minutes: Optional[int] = None,
        should_update_cache: Optional[bool] = None,
        allow_public_live_view: Optional[bool] = None,
        browser_profile_id: Optional[str] = None,
        use_proxy: Optional[bool] = None,
        proxy_city: Optional[str] = None,
        proxy_server: Optional[str] = None,
        proxy_server_username: Optional[str] = None,
        proxy_server_password: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trigger a workflow execution with the provided input variables.

        Args:
            workflow_id: The unique identifier of the workflow to start
            input_variables: Key-value pairs of input variable names and their values
            timeout_minutes: Maximum execution time in minutes
            should_update_cache: Whether to update the execution cache (default: True)
            allow_public_live_view: Enable public live viewing of the workflow execution (default: False)
            browser_profile_id: UUID of a browser profile to use for this workflow execution
            use_proxy: Enable proxy for browser sessions in this workflow
            proxy_city: Proxy location (New York, Los Angeles, Chicago, Seattle, Miami, Toronto, London, Frankfurt, Singapore, Sydney)
            proxy_server: Custom proxy server URL (e.g., http://proxy.example.com:8080)
            proxy_server_username: Username for custom proxy server authentication
            proxy_server_password: Password for custom proxy server authentication
            user_agent: Custom user agent string for browser sessions

        Returns:
            Dict containing workflow_execution_id and status
        """

        payload: Dict[str, Any] = {"input_variables": dict(input_variables)}
        if timeout_minutes is not None:
            payload["timeout_minutes"] = timeout_minutes
        if should_update_cache is not None:
            payload["should_update_cache"] = should_update_cache
        if allow_public_live_view is not None:
            payload["allow_public_live_view"] = allow_public_live_view
        if browser_profile_id is not None:
            payload["browser_profile_id"] = browser_profile_id
        if use_proxy is not None:
            payload["use_proxy"] = use_proxy
        if proxy_city is not None:
            payload["proxy_city"] = proxy_city
        if proxy_server is not None:
            payload["proxy_server"] = proxy_server
        if proxy_server_username is not None:
            payload["proxy_server_username"] = proxy_server_username
        if proxy_server_password is not None:
            payload["proxy_server_password"] = proxy_server_password
        if user_agent is not None:
            payload["user_agent"] = user_agent
        return self._request("POST", f"/public/workflows/start/{workflow_id}", json=payload)

    def list_workflow_executions(self, workflow_id: str) -> Dict[str, Any]:
        """Return executions for the given workflow."""

        return self._request("GET", f"/public/workflows/{workflow_id}")

    def get_execution_details(self, workflow_id: str, execution_id: str) -> Dict[str, Any]:
        """Fetch detailed information about a workflow execution."""

        return self._request("GET", f"/public/workflows/{workflow_id}/executions/{execution_id}")

    def resume_workflow(self, resume_url: str, variables: Mapping[str, Any]) -> Dict[str, Any]:
        """Resume a paused workflow using the resume URL from a webhook payload."""

        payload = {"variables": dict(variables)}
        return self._request("POST", resume_url, json=payload, require_api_key=False)

    # ------------------------------------------------------------------
    # Account metadata
    # ------------------------------------------------------------------
    def list_credentials(self) -> Any:
        """Return saved browser credentials."""

        return self._request("GET", "/public/credentials")

    def create_credential(
        self,
        *,
        service_name: str,
        username_or_email: Optional[str] = None,
        password: Optional[str] = None,
        totp_secret: Optional[str] = None,
        gmail_oauth_account_id: Optional[str] = None,
        phone_number_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new credential with API key authentication."""

        payload: Dict[str, Any] = {"service_name": service_name}
        if username_or_email is not None:
            payload["username_or_email"] = username_or_email
        if password is not None:
            payload["password"] = password
        if totp_secret is not None:
            payload["totp_secret"] = totp_secret
        if gmail_oauth_account_id is not None:
            payload["gmail_oauth_account_id"] = gmail_oauth_account_id
        if phone_number_id is not None:
            payload["phone_number_id"] = phone_number_id
        return self._request("POST", "/public/credentials", json=payload)

    def list_connected_accounts(self) -> Any:
        """Return OAuth accounts associated with the workspace."""

        return self._request("GET", "/public/connected-accounts")

    def list_phone_numbers(self) -> Any:
        """Return all phone numbers for the workspace."""

        return self._request("GET", "/public/phone-numbers")

    def purchase_phone_number(self, *, label: str) -> Dict[str, Any]:
        """Purchase a new Twilio phone number for the workspace."""

        payload = {"label": label}
        return self._request("POST", "/public/phone-numbers", json=payload)

    def create_browser_profile(
        self,
        *,
        name: str,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new browser profile to persist cookies, login sessions, and browser state.

        Args:
            name: A unique name for the browser profile
            provider: Browser provider to use (hyperbrowser or kernel), defaults to hyperbrowser

        Returns:
            Dict containing id, name, and created_at
        """

        payload: Dict[str, Any] = {"name": name}
        if provider is not None:
            payload["provider"] = provider
        return self._request("POST", "/public/browser-profiles", json=payload)

    def list_browser_profiles(self) -> Dict[str, Any]:
        """Return all browser profiles in the workspace.

        Returns:
            Dict containing profiles array with id, name, and created_at for each profile
        """

        return self._request("GET", "/public/browser-profiles")

    # ------------------------------------------------------------------
    # Computer use helpers
    # ------------------------------------------------------------------
    def run_single_action(
        self,
        *,
        action: str,
        session_id: Optional[str] = None,
        id: Optional[str] = None,
        variables: Optional[Mapping[str, Any]] = None,
        screen_config: Optional[Mapping[str, Any]] = None,
        set_cache: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Execute a single action with the Computer Use agent.

        Args:
            action: The action to perform
            session_id: Optional existing session ID to use. If not provided, auto-creates a 10-min session
            id: Optional ID for caching the step instance
            variables: Optional variables for the action
            screen_config: Screen configuration (only used when auto-creating session)
            set_cache: Whether to cache the result

        Returns:
            Dict containing success, result, credits, error, and cache info
        """

        payload: Dict[str, Any] = {
            "action": action,
        }
        if session_id is not None:
            payload["session_id"] = session_id
        if id is not None:
            payload["id"] = id
        if variables is not None:
            payload["variables"] = dict(variables)
        if screen_config is not None:
            payload["screen_config"] = dict(screen_config)
        if set_cache is not None:
            payload["set_cache"] = set_cache
        return self._request("POST", "/public/single-actions/run-action", json=payload, timeout=120)

    # ------------------------------------------------------------------
    # Browser session management
    # ------------------------------------------------------------------
    def create_session(
        self,
        *,
        cdp_url: Optional[str] = None,
        screen_config: Optional[Mapping[str, Any]] = None,
        ttl: Optional[int] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a managed browser session.

        Args:
            cdp_url: Optional external CDP URL to bring your own browser
            screen_config: Screen configuration (width, height)
            ttl: Time-to-live in seconds, max 86400 (24 hours)
            metadata: Optional custom metadata

        Returns:
            Dict containing session_id, cdp_url, screen_config, status, expires_at, metadata, created_at, updated_at
        """

        payload: Dict[str, Any] = {}
        if cdp_url is not None:
            payload["cdp_url"] = cdp_url
        if screen_config is not None:
            payload["screen_config"] = dict(screen_config)
        if ttl is not None:
            payload["ttl"] = ttl
        if metadata is not None:
            payload["metadata"] = dict(metadata)
        return self._request("POST", "/public/sessions", json=payload)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get details of a specific session.

        Args:
            session_id: The session ID to retrieve

        Returns:
            Dict containing session details
        """

        return self._request("GET", f"/public/sessions/{session_id}")

    def list_sessions(
        self,
        *,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List all sessions.

        Args:
            status_filter: Optional status filter (e.g., 'active')
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            Dict containing sessions list and total count
        """

        params: Dict[str, Any] = {}
        if status_filter is not None:
            params["status_filter"] = status_filter
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        return self._request("GET", "/public/sessions", params=params if params else None)

    def update_session(
        self,
        session_id: str,
        *,
        ttl: Optional[int] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update a session's TTL or metadata.

        Args:
            session_id: The session ID to update
            ttl: Optional new TTL in seconds to extend expiration
            metadata: Optional metadata to merge with existing metadata

        Returns:
            Dict containing updated session details
        """

        payload: Dict[str, Any] = {}
        if ttl is not None:
            payload["ttl"] = ttl
        if metadata is not None:
            payload["metadata"] = dict(metadata)
        return self._request("PATCH", f"/public/sessions/{session_id}", json=payload)

    def terminate_session(self, session_id: str) -> None:
        """Terminate a session.

        Args:
            session_id: The session ID to terminate
        """

        self._request("POST", f"/public/sessions/{session_id}/terminate")

    def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: The session ID to delete
        """

        self._request("DELETE", f"/public/sessions/{session_id}")

    # ------------------------------------------------------------------
    # Session helpers
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the underlying :class:`requests.Session`."""

        self._session.close()

    def __enter__(self) -> "Dari":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        require_api_key: bool = True,
        timeout: Optional[int | float] = None,
    ) -> Any:
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        else:
            url = f"{self.base_url}{path_or_url}"
        request_headers: MutableMapping[str, str] = dict(self._default_headers)
        if not require_api_key:
            request_headers.pop("X-API-Key", None)
        if headers:
            request_headers.update(headers)
        if json is not None:
            request_headers.setdefault("Content-Type", "application/json")
        try:
            response = self._session.request(
                method,
                url,
                json=json,
                params=params,
                headers=request_headers,
                timeout=timeout if timeout is not None else self.timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - simple passthrough
            raise DariError(str(exc)) from exc
        if response.status_code >= 400:
            raise DariError(self._build_error_message(response), status_code=response.status_code, response=response)
        if response.status_code == 204 or not response.content:
            return None
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                return response.json()
            except ValueError as exc:
                raise DariError("Invalid JSON received from Dari", status_code=response.status_code, response=response) from exc
        return response.text

    @staticmethod
    def _build_error_message(response: Response) -> str:
        try:
            data = response.json()
        except ValueError:
            return f"Dari request failed with status {response.status_code}: {response.text}"
        if isinstance(data, dict):
            for key in ("detail", "error", "message"):
                if key in data and data[key]:
                    return str(data[key])
        return f"Dari request failed with status {response.status_code}"
