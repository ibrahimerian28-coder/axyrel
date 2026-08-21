from __future__ import annotations
from datetime import date
import streamlit as st
from utils.api_client import request
from utils.ui import api_call, money


def app() -> None:
    st.title("📈 Profitability")
    c1,c2=st.columns(2); start=c1.date_input("From",value=date(date.today().year,1,1)); end=c2.date_input("To",value=date.today())
    summary=api_call(lambda: request("GET","/profitability/summary",params={"start_date":start.isoformat(),"end_date":end.isoformat()}))
    if not summary: st.info("No profitability data yet."); return
    cols=st.columns(4)
    cols[0].metric("Invoiced revenue",money(summary.get("invoiced_revenue")))
    cols[1].metric("Collected",money(summary.get("collected_revenue")))
    cols[2].metric("Expenses",money(summary.get("expenses")))
    cols[3].metric("Net profit",money(summary.get("net_profit")))
    st.metric("Profit margin",f"{summary.get('profit_margin_percent',0)}%")
    breakdown=api_call(lambda: request("GET","/profitability/expenses",params={"start_date":start.isoformat(),"end_date":end.isoformat()})) or []
    if breakdown: st.bar_chart({x.get("category"):float(x.get("amount",0)) for x in breakdown})
