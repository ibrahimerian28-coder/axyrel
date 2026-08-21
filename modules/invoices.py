from __future__ import annotations
from datetime import date
import streamlit as st
from utils.api_client import create_record, delete_record, list_records
from utils.ui import api_call, as_frame, money


def app() -> None:
    st.title("🧾 Invoices")
    customers=api_call(list_records,"customers") or []
    invoices=api_call(list_records,"invoices") or []
    with st.expander("➕ Create invoice"):
        if not customers: st.info("Create a customer first.")
        else:
            labels={f"#{c.get('display_id') or '-'} · {c.get('name')}":c for c in customers}
            with st.form("invoice"):
                label=st.selectbox("Customer",list(labels)); number=st.text_input("Invoice number *"); issue=st.date_input("Issue date",value=date.today()); due=st.date_input("Due date",value=date.today()); subtotal=st.number_input("Subtotal",min_value=0.0,step=50.0); discount=st.number_input("Discount",min_value=0.0,step=10.0); tax=st.number_input("Tax",min_value=0.0,step=10.0); paid=st.number_input("Paid amount",min_value=0.0,step=10.0); notes=st.text_area("Notes")
                if st.form_submit_button("Save invoice",type="primary"):
                    total=max(0,subtotal-discount+tax); c=labels[label]; payload={"customer_id":c["id"],"invoice_number":number,"status":"Draft","issue_date":issue.isoformat(),"due_date":due.isoformat(),"subtotal":subtotal,"discount":discount,"tax":tax,"total":total,"paid_amount":paid,"notes":notes or None}
                    if api_call(create_record,"invoices",payload) is not None: st.success("Invoice created."); st.rerun()
    st.dataframe(as_frame(invoices),use_container_width=True,hide_index=True)
    for inv in invoices:
        iid=str(inv["id"])
        if st.button(f"Delete invoice {inv.get('invoice_number')}",key=f"delinv_{iid}"):
            if api_call(delete_record,"invoices",iid) is None: st.success("Deleted."); st.rerun()
