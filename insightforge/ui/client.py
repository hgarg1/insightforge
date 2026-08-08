"""Small typed HTTP client used by the shared Flet UI."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

_STATUS_FALLBACKS = {
    400: "Please check the information and try again.",
    401: "Your session has expired. Please sign in again.",
    403: "You do not have permission to do that.",
    404: "We could not find that item. Refresh and try again.",
    409: "That already exists. Try a different value.",
    413: "That file is too large. Choose a smaller workbook and try again.",
    422: "Please check the highlighted information and try again.",
}


def _fallback_message(status_code: int | None) -> str:
    if status_code and status_code >= 500:
        return "Something went wrong on our side. Please try again."
    return _STATUS_FALLBACKS.get(status_code, "The request could not be completed. Please try again.")


def _clean_message(value: str) -> str:
    """Return display-safe text without leaking raw response bodies into the UI."""

    compact = " ".join(value.split())
    return compact[:360]


def _field_label(location: Any) -> str:
    if not isinstance(location, (list, tuple)):
        return ""
    parts = [str(part) for part in location if str(part) not in {"body", "query", "path", "header"}]
    if not parts:
        return ""
    return parts[-1].replace("_", " ").capitalize()


def _humanize_error(payload: Any, status_code: int | None = None) -> str:
    """Flatten FastAPI and Pydantic errors into short, useful interface copy."""

    fallback = _fallback_message(status_code)
    if isinstance(payload, str):
        message = _clean_message(payload)
        if not message:
            return fallback
        # Some endpoints return JSON as text (notably binary download endpoints).
        if message.startswith(("{", "[")):
            try:
                return _humanize_error(json.loads(message), status_code)
            except json.JSONDecodeError:
                return fallback
        return message
    if isinstance(payload, dict):
        for key in ("detail", "message", "error"):
            if key in payload:
                return _humanize_error(payload[key], status_code)
        return fallback
    if isinstance(payload, list):
        messages: list[str] = []
        for item in payload:
            if isinstance(item, dict):
                detail = item.get("msg") or item.get("message") or item.get("detail")
                if isinstance(detail, str) and _clean_message(detail):
                    prefix = _field_label(item.get("loc"))
                    message = _clean_message(detail)
                    messages.append(f"{prefix}: {message}" if prefix else message)
            else:
                message = _humanize_error(item, status_code)
                if message != fallback:
                    messages.append(message)
        if messages:
            return " ".join(dict.fromkeys(messages))[:360]
    return fallback


def _response_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except (ValueError, json.JSONDecodeError):
        payload = response.text
    return _humanize_error(payload, response.status_code)


class ApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ApiClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = (
            base_url or os.getenv("INSIGHTFORGE_API_URL", "http://127.0.0.1:8765")
        ).rstrip("/")
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.user: dict[str, Any] | None = None

    @property
    def authenticated(self) -> bool:
        return bool(self.access_token and self.user)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = dict(kwargs.pop("headers", {}) or {})
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        try:
            response = httpx.request(
                method, f"{self.base_url}{path}", headers=headers, timeout=90, **kwargs
            )
        except httpx.HTTPError as exc:
            raise ApiError(f"Could not reach the InsightForge service: {exc}") from exc
        if response.status_code == 401 and self.refresh_token and path != "/api/auth/refresh":
            try:
                self._refresh()
                headers["Authorization"] = f"Bearer {self.access_token}"
                response = httpx.request(
                    method, f"{self.base_url}{path}", headers=headers, timeout=90, **kwargs
                )
            except ApiError:
                pass
        if response.status_code >= 400:
            raise ApiError(_response_error(response), response.status_code)
        if response.status_code == 204:
            return None
        return response.json()

    def _set_tokens(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.access_token = payload["access_token"]
        self.refresh_token = payload["refresh_token"]
        self.user = payload["user"]
        return payload

    def signup(self, email: str, full_name: str, password: str) -> dict[str, Any]:
        return self._set_tokens(
            self._request(
                "POST",
                "/api/auth/signup",
                json={"email": email, "full_name": full_name, "password": password},
            )
        )

    def login(self, email: str, password: str) -> dict[str, Any]:
        return self._set_tokens(
            self._request("POST", "/api/auth/login", json={"email": email, "password": password})
        )

    def _refresh(self) -> None:
        if not self.refresh_token:
            raise ApiError("Your session has expired. Please sign in again.", 401)
        payload = self._request(
            "POST", "/api/auth/refresh", json={"refresh_token": self.refresh_token}
        )
        self._set_tokens(payload)

    def logout(self) -> None:
        if self.refresh_token:
            try:
                self._request(
                    "POST", "/api/auth/logout", json={"refresh_token": self.refresh_token}
                )
            except ApiError:
                pass
        self.access_token = None
        self.refresh_token = None
        self.user = None

    def request_reset(self, email: str) -> dict[str, Any]:
        return self._request("POST", "/api/auth/password-reset/request", json={"email": email})

    def confirm_reset(self, token: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST", "/api/auth/password-reset/confirm", json={"token": token, "password": password}
        )

    def datasets(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/datasets")

    def upload(
        self, filename: str, content: bytes, sheet_name: str | None = None
    ) -> dict[str, Any]:
        data = {"sheet_name": sheet_name} if sheet_name else {}
        return self._request(
            "POST",
            "/api/datasets/upload",
            data=data,
            files={
                "file": (
                    filename,
                    content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

    def dataset(self, dataset_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/datasets/{dataset_id}")

    def transform(self, dataset_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/api/datasets/{dataset_id}/transform", json=payload)

    def create_chart(self, dataset_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", f"/api/datasets/{dataset_id}/chart", json=payload)

    def dashboard(self) -> dict[str, Any]:
        return self._request("GET", "/api/dashboard")

    def save_dashboard(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("PUT", "/api/dashboard", json=payload)

    def visualizations(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/datasets/visualizations/mine")

    def export(self, dataset_id: str, file_format: str = "xlsx") -> tuple[str, bytes]:
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        try:
            response = httpx.get(
                f"{self.base_url}/api/datasets/{dataset_id}/export",
                params={"format": file_format},
                headers=headers,
                timeout=90,
            )
        except httpx.HTTPError as exc:
            raise ApiError(f"Could not reach the InsightForge service: {exc}") from exc
        if response.status_code >= 400:
            raise ApiError(_response_error(response), response.status_code)
        return f"insightforge-export.{file_format}", response.content
