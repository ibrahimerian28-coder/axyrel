"""Small Streamlit helpers for the API-backed UI."""
from __future__ import annotations

from typing import Any, Callable
import pandas as pd
import streamlit as st

from utils.api_client import APIClientError


def api_call(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any | None:
    try:
        return fn(*args, **kwargs)
    except APIClientError as exc:
        st.error(str(exc))
    return None


def as_frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def money(value: Any) -> str:
    try:
        return f"{float(value or 0):,.2f} EGP"
    except (TypeError, ValueError):
        return "0.00 EGP"
