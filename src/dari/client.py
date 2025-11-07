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
    def start_workflow(self, workflow_id: str, input_variables: Mapping[str, Any]) -> Dict[str, Any]:
        """Trigger a workflow execution with the provided input variables."""

        payload = {"input_variables": dict(input_variables)}
        return self._request("POST", f"/workflows/start/{workflow_id}", json=payload)

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

        return self._request("GET", "/credentials")

    def list_connected_accounts(self) -> Any:
        """Return OAuth accounts associated with the workspace."""

        return self._request("GET", "/connected-accounts")

    # ------------------------------------------------------------------
    # Computer use helpers
    # ------------------------------------------------------------------
    def run_single_action(
        self,
        *,
        cdp_url: str,
        action: str,
        identifier: Optional[str] = None,
        variables: Optional[Mapping[str, Any]] = None,
        screen_config: Optional[Mapping[str, Any]] = None,
        set_cache: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Execute a single action with the Computer Use agent."""

        payload: Dict[str, Any] = {
            "cdp_url": cdp_url,
            "action": action,
        }
        if identifier is not None:
            payload["id"] = identifier
        if variables is not None:
            payload["variables"] = dict(variables)
        if screen_config is not None:
            payload["screen_config"] = dict(screen_config)
        if set_cache is not None:
            payload["set_cache"] = set_cache
        return self._request("POST", "/single-actions/run-action", json=payload)

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
                timeout=self.timeout,
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
