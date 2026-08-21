"""Task 45/46 HTTP client used by the Streamlit presentation layer.

The client is the single HTTP boundary for Streamlit. Authentication is now
DB-backed through FastAPI Task 46; tenant context is derived by the API from
the authenticated user and is never sent as X-Company-ID.
"""
from __future__ import annotations

from typing import Any

import requests
import streamlit as st

from backend.core.config import settings


class APIClientError(RuntimeError):
    """Raised when the configured Axyrel API cannot complete a request."""


def api_enabled() -> bool:
    return bool(settings.ui_api_enabled)


def _session_token() -> str:
    return str(st.session_state.get("api_access_token") or settings.api_token or "")


def _headers(*, authenticated: bool = True) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if authenticated:
        token = _session_token()
        if not token:
            raise APIClientError(
                "No API access token is available. Log in through the API authentication flow."
            )
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _request(
    method: str,
    path: str,
    *,
    json: Any = None,
    data: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    authenticated: bool = True,
) -> Any:
    url = f"{settings.api_base_url.rstrip('/')}{settings.api_prefix}{path}"
    try:
        response = requests.request(
            method,
            url,
            headers=_headers(authenticated=authenticated),
            json=json,
            data=data,
            params=params,
            timeout=settings.api_timeout_seconds,
        )
    except requests.RequestException as exc:
        raise APIClientError(f"API connection failed: {exc}") from exc

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise APIClientError(f"API {response.status_code}: {detail}")

    if response.status_code == 204 or not response.content:
        return None
    return response.json()


def login(email: str, password: str) -> dict[str, Any]:
    """Authenticate against FastAPI using OAuth2 form data."""
    url = f"{settings.api_base_url.rstrip('/')}{settings.api_prefix}/auth/login"

    try:
        response = requests.post(
            url,
            headers={
                "Accept": "application/json",
            },
            data={
                "username": email.strip(),
                "password": password,
            },
            timeout=settings.api_timeout_seconds,
        )
    except requests.RequestException as exc:
        raise APIClientError(f"API connection failed: {exc}") from exc

    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise APIClientError(f"API {response.status_code}: {detail}")

    payload = response.json()

    token = payload.get("access_token") if isinstance(payload, dict) else None

    if not token:
        raise APIClientError(
            "Authentication succeeded but no access token was returned."
        )

    st.session_state.api_access_token = token

    try:
        user = me()
    except Exception:
        st.session_state.pop("api_access_token", None)
        st.session_state.pop("api_user", None)
        raise

    st.session_state.api_user = user

    return user


def logout() -> None:
    st.session_state.pop("api_access_token", None)
    st.session_state.pop("api_user", None)


def me() -> dict[str, Any]:
    payload = _request("GET", "/auth/me")
    if not isinstance(payload, dict):
        raise APIClientError("Invalid /auth/me response.")
    return payload


def request(method: str, path: str, *, json: Any = None, params: dict[str, Any] | None = None) -> Any:
    return _request(method, path, json=json, params=params)


def list_records(resource: str, *, search: str | None = None, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    query = dict(params or {})
    if search:
        query["search"] = search
    payload = request("GET", f"/{resource}", params=query or None)
    return payload if isinstance(payload, list) else []


def create_record(resource: str, payload: dict[str, Any]) -> dict[str, Any]:
    return request("POST", f"/{resource}", json=payload)


def update_record(resource: str, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return request("PATCH", f"/{resource}/{record_id}", json=payload)


def delete_record(resource: str, record_id: str) -> None:
    request("DELETE", f"/{resource}/{record_id}")
