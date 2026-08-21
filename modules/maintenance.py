from __future__ import annotations
from datetime import datetime, date, time
import streamlit as st
from utils.api_client import create_record, delete_record, list_records, request, update_record
from utils.ui import api_call, as_frame


def app() -> None:
    st.title("🔧 Maintenance & Field Service")
    customers=api_call(list_records,"customers") or []
    orders=api_call(list_records,"work-orders") or []
    visits=api_call(list_records,"service-visits") or []
    requests_=api_call(list_records,"service-requests") or []
    tabs=st.tabs(["Work Orders","Service Visits","Requests"])

    with tabs[0]:
        if customers:
            labels={f"#{c.get('display_id') or '-'} · {c.get('name')}":c for c in customers}
            with st.expander("➕ Create work order"):
                with st.form("wo"):
                    label=st.selectbox("Customer",list(labels)); title=st.text_input("Title *"); desc=st.text_area("Description"); priority=st.selectbox("Priority",["Low","Normal","High","Urgent"]); status=st.selectbox("Status",["Open","In Progress","Completed","Cancelled"]); notes=st.text_area("Notes")
                    if st.form_submit_button("Create",type="primary"):
                        payload={"customer_id":labels[label]["id"],"title":title,"description":desc or None,"priority":priority,"status":status,"notes":notes or None}
                        if api_call(create_record,"work-orders",payload) is not None: st.success("Work order created."); st.rerun()
        for o in orders:
            oid=str(o["id"])
            with st.expander(f"#{o.get('display_id') or '-'} · {o.get('title')} · {o.get('status')}"):
                st.write(o.get("description") or "-")
                new_status=st.selectbox("Status",["Open","In Progress","Completed","Cancelled"],index=["Open","In Progress","Completed","Cancelled"].index(o.get("status")) if o.get("status") in {"Open","In Progress","Completed","Cancelled"} else 0,key=f"wos_{oid}")
                c1,c2=st.columns(2)
                if c1.button("Update",key=f"wou_{oid}"):
                    if api_call(update_record,"work-orders",oid,{"status":new_status}) is not None: st.success("Updated."); st.rerun()
                if c2.button("Delete",key=f"wod_{oid}"):
                    if api_call(delete_record,"work-orders",oid) is None: st.success("Deleted."); st.rerun()

    with tabs[1]:
        if orders and customers:
            order_labels={f"#{o.get('display_id') or '-'} · {o.get('title')}":o for o in orders}
            customer_map={str(c["id"]):c for c in customers}
            with st.expander("➕ Record field visit"):
                with st.form("visit"):
                    ol=st.selectbox("Work order",list(order_labels)); status=st.selectbox("Status",["Planned","In Progress","Completed","Cancelled"]); notes=st.text_area("Visit notes")
                    if st.form_submit_button("Save visit",type="primary"):
                        o=order_labels[ol]; payload={"work_order_id":o["id"],"customer_id":o["customer_id"],"asset_id":o.get("asset_id"),"status":status,"notes":notes or None}
                        if api_call(create_record,"service-visits",payload) is not None: st.success("Visit recorded."); st.rerun()
        for v in visits:
            vid=str(v["id"])
            with_label=f"{v.get('status')} · {v.get('actual_start_at') or 'not started'}"
            with st.expander(with_label):
                st.write(f"Customer ID: {v.get('customer_id')} · Work order: {v.get('work_order_id')}")
                if st.button("Delete visit",key=f"vd_{vid}"):
                    if api_call(delete_record,"service-visits",vid) is None: st.success("Deleted."); st.rerun()

    with tabs[2]:
        st.dataframe(as_frame(requests_),use_container_width=True,hide_index=True)
        if customers:
            labels={f"#{c.get('display_id') or '-'} · {c.get('name')}":c for c in customers}
            with st.expander("➕ Create service request"):
                with st.form("request"):
                    label=st.selectbox("Customer",list(labels)); title=st.text_input("Request title *"); desc=st.text_area("Description"); priority=st.selectbox("Priority",["Low","Normal","High","Urgent"])
                    if st.form_submit_button("Create request",type="primary"):
                        payload={"customer_id":labels[label]["id"],"title":title,"description":desc or None,"priority":priority,"status":"Open","source":"Streamlit"}
                        if api_call(create_record,"service-requests",payload) is not None: st.success("Request created."); st.rerun()
