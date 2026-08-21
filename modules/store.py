from __future__ import annotations
import streamlit as st
from utils.api_client import list_records
from utils.ui import api_call, as_frame, money


def app() -> None:
    st.title("🛒 Store / Catalog")
    st.caption("The current MVP uses inventory as the product catalog. Full customer checkout/order management is not part of the frozen MVP backend yet.")
    items = api_call(list_records, "inventory") or []
    if not items:
        st.info("No catalog items yet. Add items from Inventory.")
        return
    df = as_frame(items)
    df = df[[c for c in ["item_name","quantity","cost_price","status"] if c in df.columns]]
    if "cost_price" in df.columns:
        df["cost_price"] = df["cost_price"].map(money)
    st.dataframe(df, use_container_width=True, hide_index=True)
