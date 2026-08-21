from __future__ import annotations
import streamlit as st
from utils.api_client import create_record, delete_record, list_records, request, update_record
from utils.ui import api_call, as_frame, money


def app() -> None:
    st.title("📦 Inventory")
    items = api_call(list_records, "inventory") or []
    df = as_frame(items)
    if not df.empty:
        df["stock_value"] = df["quantity"] * df["cost_price"]
    low = sum(int(i.get("quantity", 0)) <= int(i.get("min_limit", 0)) for i in items)
    total_value = sum(float(i.get("quantity", 0)) * float(i.get("cost_price", 0)) for i in items)
    c1,c2,c3 = st.columns(3); c1.metric("Items", len(items)); c2.metric("Low stock", low); c3.metric("Stock value", money(total_value))

    with st.expander("➕ Add inventory item"):
        with st.form("add_inventory"):
            name = st.text_input("Item name *")
            qty = st.number_input("Quantity", min_value=0, step=1)
            min_limit = st.number_input("Minimum stock", min_value=0, step=1)
            ideal = st.number_input("Ideal stock", min_value=0, step=1)
            cost = st.number_input("Cost price", min_value=0.0, step=10.0)
            status = st.selectbox("Status", ["Active", "Inactive"])
            if st.form_submit_button("Save", type="primary"):
                if not name.strip(): st.error("Item name is required.")
                else:
                    payload={"item_name":name.strip(),"quantity":int(qty),"min_limit":int(min_limit),"ideal_stock":int(ideal),"cost_price":cost,"status":status}
                    if api_call(create_record,"inventory",payload) is not None: st.success("Item created."); st.rerun()

    search = st.text_input("🔍 Search item")
    if search: items = api_call(list_records,"inventory",search=search) or []
    for item in items:
        iid=str(item["id"]); qty=int(item.get("quantity",0)); minimum=int(item.get("min_limit",0))
        with st.expander(f"{item.get('item_name','')} · Qty {qty} · {'🔴 Low' if qty <= minimum else '🟢 Good'}"):
            st.write(f"Cost: {money(item.get('cost_price'))} · Min: {minimum} · Ideal: {item.get('ideal_stock',0)}")
            c1,c2,c3=st.columns(3)
            with c1:
                amount=st.number_input("Movement quantity",min_value=1,step=1,key=f"mvqty_{iid}")
                typ=st.selectbox("Movement",["IN","OUT","ADJUSTMENT"],key=f"mvtype_{iid}")
                if st.button("Post movement",key=f"mv_{iid}"):
                    payload={"inventory_item_id":iid,"transaction_type":typ,"quantity":int(amount),"reference_type":"streamlit"}
                    if api_call(lambda p: request("POST","/inventory-transactions",json=p),payload) is not None:
                        st.success("Movement posted."); st.rerun()
            with c2:
                if st.button("Delete",key=f"delinv_{iid}"):
                    if api_call(delete_record,"inventory",iid) is None: st.success("Item deleted."); st.rerun()
            with c3:
                with st.form(f"editinv_{iid}"):
                    new_qty=st.number_input("Set quantity",min_value=0,value=qty,key=f"setqty_{iid}")
                    new_min=st.number_input("Set minimum",min_value=0,value=minimum,key=f"setmin_{iid}")
                    if st.form_submit_button("Update"):
                        if api_call(update_record,"inventory",iid,{"quantity":int(new_qty),"min_limit":int(new_min)}) is not None: st.success("Updated."); st.rerun()

    with st.expander("📜 Inventory transaction history"):
        tx = api_call(lambda: request("GET","/inventory-transactions")) or []
        st.dataframe(as_frame(tx), use_container_width=True, hide_index=True)
