"""Data access facade for the legacy Streamlit UI.

Task 45 adds an opt-in FastAPI path. When AXYREL_UI_API_ENABLED=true, supported
migrated domains use the Axyrel API instead of Google Sheets. Unsupported legacy
screens continue to use their existing data source until their UI migration.
"""
from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

from backend.core.config import settings
from utils.api_client import APIClientError, api_enabled, create_record, delete_record, list_records, update_record

SHEET_ID = "1RGDGJaP_lo2Fp2beLqAQvLulqMk2WDJKqLv2g34-ycc"
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzl-pbbFkqngGlP-WOzHJdU3NZhnjWQUFw_zFxodqwNFXZC6EdrrSuIJItyIjU-pzw/exec"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Only domains whose Task 44 API and UI data shape are stable are switched here.
API_SHEETS = {
    "Customers": "customers",
    "Inventory": "inventory",
    "Expenses": "expenses",
}


def _api_frame(sheet: str) -> pd.DataFrame:
    resource = API_SHEETS[sheet]
    rows = list_records(resource)
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Preserve the column names expected by existing Streamlit components.
    if sheet == "Customers":
        df = df.rename(columns={"id": "uuid"})
    elif sheet == "Inventory":
        df = df.rename(columns={
            "id": "uuid",
            "name": "item_name",
            "unit_cost": "cost_price",
            "reorder_level": "min_limit",
        })
        if "ideal_stock" not in df.columns:
            df["ideal_stock"] = df.get("min_limit", 0)
    return df.fillna("")


def load_sheet(gid):
    sheet = next((name for name, resource in API_SHEETS.items() if str(gid) == str(st.session_state.get("SHEETS", {}).get(name))), None)
    if api_enabled() and sheet:
        return _api_frame(sheet)

    url = f"{BASE_URL}&gid={gid}"
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df.fillna("")
    except Exception as e:
        print("LOAD ERROR:", e)
        return pd.DataFrame()


def call_api(action, sheet, data=None, row_index=None, uuid=None):
    if api_enabled() and sheet in API_SHEETS:
        try:
            resource = API_SHEETS[sheet]
            if action == "append":
                payload = _legacy_payload_to_api(sheet, data)
                create_record(resource, payload)
                return True
            if action == "update":
                record_id = _resolve_record_id(sheet, uuid, data)
                if not record_id:
                    return False
                payload = _legacy_payload_to_api(sheet, data, partial=True)
                update_record(resource, record_id, payload)
                return True
            if action == "delete":
                record_id = _resolve_record_id(sheet, uuid, None)
                if not record_id:
                    return False
                delete_record(resource, record_id)
                return True
            return False
        except (APIClientError, ValueError, TypeError) as exc:
            print("API ERROR:", exc)
            return False

    payload = {"action": action, "sheet": sheet, "data": data, "row_index": row_index, "uuid": uuid}
    try:
        r = requests.post(APP_SCRIPT_URL, json=payload, timeout=20)
        return r.text.strip().startswith("OK")
    except Exception as e:
        print("API ERROR:", e)
        return False


def _legacy_payload_to_api(sheet: str, data, partial: bool = False) -> dict:
    if isinstance(data, dict):
        payload = dict(data)
    else:
        values = list(data or [])
        if sheet == "Customers":
            names = ["name", "unused", "unused2", "uuid", "phone", "phone_1", "phone_2", "phone_3", "phone_4", "address", "area", "location_url", "install_date", "cycle", "device_type", "status"]
            payload = {k: v for k, v in zip(names, values) if k not in {"unused", "unused2"}}
        else:
            raise ValueError(f"Positional API payload is unsupported for {sheet}")

    if sheet == "Inventory":
        rename = {"item_name": "name", "cost_price": "unit_cost", "min_limit": "reorder_level"}
        payload = {rename.get(k, k): v for k, v in payload.items()}
        payload.pop("ideal_stock", None)
        payload.setdefault("sku", str(payload.get("name", "ITEM")))
    if sheet == "Customers":
        payload.pop("uuid", None)
        payload.pop("display_id", None)
    payload.pop("id", None)
    payload.pop("company_id", None)
    return payload


def _resolve_record_id(sheet: str, uuid_value, data) -> str | None:
    if uuid_value:
        return str(uuid_value)
    if sheet == "Inventory" and isinstance(data, dict) and data.get("item_name"):
        rows = list_records("inventory", search=str(data["item_name"]))
        exact = next((r for r in rows if str(r.get("name", "")).strip() == str(data["item_name"]).strip()), None)
        return str(exact["id"]) if exact else None
    return None


def add_row(sheet, data):
    return call_api("append", sheet, data=data)


def update_row(sheet, uuid_value, data):
    return call_api("update", sheet, data=data, uuid=uuid_value)


def delete_row_by_uuid(sheet, uuid_value):
    return call_api("delete", sheet, uuid=uuid_value)
