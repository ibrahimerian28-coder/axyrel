from __future__ import annotations
from datetime import date
import streamlit as st
from utils.api_client import create_record, delete_record, list_records, update_record
from utils.ui import api_call, as_frame, money


def app() -> None:
    st.title("💵 Expenses")
    expenses=api_call(list_records,"expenses") or []
    total=sum(float(x.get("amount",0)) for x in expenses)
    c1,c2=st.columns(2); c1.metric("Expenses",len(expenses)); c2.metric("Total",money(total))
    with st.expander("➕ Add expense"):
        with st.form("add_expense"):
            category=st.text_input("Category *"); desc=st.text_input("Description"); amount=st.number_input("Amount",min_value=0.0,step=10.0); d=st.date_input("Date",value=date.today()); method=st.selectbox("Payment method",["Cash","Bank","Card","Transfer","Other"]); vendor=st.text_input("Vendor"); notes=st.text_area("Notes")
            if st.form_submit_button("Save",type="primary"):
                payload={"category":category,"description":desc or None,"amount":amount,"expense_date":d.isoformat(),"payment_method":method,"vendor":vendor or None,"notes":notes or None}
                if api_call(create_record,"expenses",payload) is not None: st.success("Expense created."); st.rerun()
    if not expenses: st.info("No expenses recorded."); return
    st.dataframe(as_frame(expenses),use_container_width=True,hide_index=True)
    for x in expenses:
        eid=str(x["id"])
        with st.expander(f"{x.get('expense_date')} · {x.get('category')} · {money(x.get('amount'))}"):
            if st.button("Delete",key=f"delexp_{eid}"):
                if api_call(delete_record,"expenses",eid) is None: st.success("Deleted."); st.rerun()
