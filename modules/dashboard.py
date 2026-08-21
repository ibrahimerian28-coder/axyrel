from __future__ import annotations
import streamlit as st
from utils.api_client import list_records, request
from utils.ui import api_call, money


def app() -> None:
    st.title("📊 Axyrel Dashboard")
    customers=api_call(list_records,"customers") or []
    inventory=api_call(list_records,"inventory") or []
    work_orders=api_call(list_records,"work-orders") or []
    visits=api_call(list_records,"service-visits") or []
    summary=api_call(lambda: request("GET","/profitability/summary")) or {}
    c=st.columns(5)
    c[0].metric("Customers",len(customers)); c[1].metric("Inventory items",len(inventory)); c[2].metric("Open work orders",sum(x.get("status") not in {"Completed","Closed","Deleted"} for x in work_orders)); c[3].metric("Service visits",len(visits)); c[4].metric("Net profit",money(summary.get("net_profit")))
    st.divider()
    st.subheader("System status")
    st.success("FastAPI + PostgreSQL data layer is active for this session.")
    st.info("The dashboard is now backed by PostgreSQL/FastAPI; no Google Sheets calls are used in the MVP UI.")
