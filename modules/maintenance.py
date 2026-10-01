from __future__ import annotations
import streamlit as st
from utils.api_client import create_record, delete_record, list_records, request, update_record
from utils.ui import api_call, as_frame


VISIT_STATUSES = ["Planned", "In Progress", "Completed", "Cancelled"]
WORK_ORDER_STATUSES = ["Open", "In Progress", "Completed", "Cancelled"]


def app() -> None:
    st.title("🔧 Maintenance & Field Service")
    customers=api_call(list_records,"customers") or []
    orders=api_call(list_records,"work-orders") or []
    visits=api_call(list_records,"service-visits") or []
    requests_=api_call(list_records,"service-requests") or []
    inventory=api_call(list_records,"inventory") or []
    tabs=st.tabs(["Work Orders","Service Visits","Requests"])

    with tabs[0]:
        if customers:
            labels={f"#{c.get('display_id') or '-'} · {c.get('name')}":c for c in customers}
            with st.expander("➕ Create work order"):
                with st.form("wo"):
                    label=st.selectbox("Customer",list(labels)); title=st.text_input("Title *"); desc=st.text_area("Description"); priority=st.selectbox("Priority",["Low","Normal","High","Urgent"]); status=st.selectbox("Status",WORK_ORDER_STATUSES); notes=st.text_area("Notes")
                    if st.form_submit_button("Create",type="primary"):
                        payload={"customer_id":labels[label]["id"],"title":title,"description":desc or None,"priority":priority,"status":status,"notes":notes or None}
                        if api_call(create_record,"work-orders",payload) is not None: st.success("Work order created."); st.rerun()
        for o in orders:
            oid=str(o["id"])
            with st.expander(f"#{o.get('display_id') or '-'} · {o.get('title')} · {o.get('status')}"):
                st.write(o.get("description") or "-")
                related=[v for v in visits if str(v.get("work_order_id"))==oid]
                if related:
                    st.caption("Linked visits: " + ", ".join(f"{v.get('status')}" for v in related))
                new_status=st.selectbox("Status",WORK_ORDER_STATUSES,index=WORK_ORDER_STATUSES.index(o.get("status")) if o.get("status") in WORK_ORDER_STATUSES else 0,key=f"wos_{oid}")
                c1,c2=st.columns(2)
                if c1.button("Update",key=f"wou_{oid}"):
                    if api_call(update_record,"work-orders",oid,{"status":new_status}) is not None: st.success("Updated."); st.rerun()
                if c2.button("Delete",key=f"wod_{oid}"):
                    if api_call(delete_record,"work-orders",oid) is None: st.success("Deleted."); st.rerun()

    with tabs[1]:
        if orders and customers:
            order_labels={f"#{o.get('display_id') or '-'} · {o.get('title')}":o for o in orders}
            with st.expander("➕ Record field visit"):
                with st.form("visit"):
                    ol=st.selectbox("Work order",list(order_labels)); status=st.selectbox("Status",VISIT_STATUSES); notes=st.text_area("Visit notes")
                    if st.form_submit_button("Save visit",type="primary"):
                        o=order_labels[ol]; payload={"work_order_id":o["id"],"customer_id":o["customer_id"],"asset_id":o.get("asset_id"),"technician_id":o.get("assigned_technician_id"),"status":status,"notes":notes or None}
                        if api_call(create_record,"service-visits",payload) is not None: st.success("Visit recorded."); st.rerun()
        order_map={str(o["id"]):o for o in orders}
        item_labels={f"{i.get('item_name')} · warehouse {i.get('quantity')}":i for i in inventory}
        for v in visits:
            vid=str(v["id"])
            wo=order_map.get(str(v.get("work_order_id")))
            wo_label=f"#{wo.get('display_id')} · {wo.get('title')}" if wo else str(v.get("work_order_id"))
            with_label=f"{v.get('status')} · {wo_label}"
            with st.expander(with_label):
                st.write(f"Customer ID: {v.get('customer_id')} · Work order: {v.get('work_order_id')}")
                st.caption(f"Technician: {v.get('technician_id') or (wo or {}).get('assigned_technician_id') or 'unassigned'}")
                current=v.get("status") if v.get("status") in VISIT_STATUSES else "Planned"
                new_status=st.selectbox("Visit status",VISIT_STATUSES,index=VISIT_STATUSES.index(current),key=f"vs_{vid}")
                if st.button("Update visit",key=f"vu_{vid}"):
                    if api_call(update_record,"service-visits",vid,{"status":new_status}) is not None: st.success("Visit updated."); st.rerun()
                if item_labels:
                    part_label=st.selectbox("Install part from technician stock",list(item_labels),key=f"vp_{vid}")
                    qty=st.number_input("Quantity",min_value=1,step=1,key=f"vq_{vid}")
                    if st.button("Install part",key=f"vi_{vid}"):
                        item=item_labels[part_label]
                        result=api_call(lambda: request("POST",f"/service-visits/{vid}/parts",json={"inventory_item_id":item["id"],"quantity":int(qty)}))
                        if result is not None: st.success("Part deducted from technician inventory."); st.rerun()
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
