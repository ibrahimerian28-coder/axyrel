from __future__ import annotations

from datetime import date
import streamlit as st

from utils.api_client import create_record, delete_record, list_records, update_record
from utils.constants import AREAS, CUSTOMER_STATUS, DEVICE_TYPES
from utils.ui import api_call, as_frame


def _customer_label(c: dict) -> str:
    return f"#{c.get('display_id') or '-'} · {c.get('name', '')} · {c.get('phone') or 'no phone'}"


def app() -> None:
    st.title("👥 Customers")
    customers = api_call(list_records, "customers", search=st.session_state.get("customer_search")) or []
    df = as_frame(customers)

    with st.expander("➕ Add Customer", expanded=False):
        with st.form("add_customer"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name *")
            phone = c2.text_input("Phone")
            phone_1 = c1.text_input("Phone 1")
            phone_2 = c2.text_input("Phone 2")
            phone_3 = c1.text_input("Phone 3")
            phone_4 = c2.text_input("Phone 4")
            address = st.text_input("Address")
            area = st.selectbox("Area", AREAS)
            if area == "Other": area = st.text_input("New area")
            location_url = st.text_input("Google Maps URL")
            install_date = st.date_input("Install date", value=None)
            cycle = st.text_input("Maintenance cycle (months)")
            device_type = st.selectbox("Device type", DEVICE_TYPES)
            if device_type == "Other": device_type = st.text_input("New device type")
            status = st.selectbox("Status", CUSTOMER_STATUS)
            if st.form_submit_button("Save Customer", type="primary"):
                if not name.strip():
                    st.error("Name is required.")
                else:
                    payload = {"name": name.strip(), "phone": phone or None, "phone_1": phone_1 or None, "phone_2": phone_2 or None, "phone_3": phone_3 or None, "phone_4": phone_4 or None, "address": address or None, "area": area or None, "location_url": location_url or None, "install_date": install_date.isoformat() if install_date else None, "cycle": cycle or None, "device_type": device_type or None, "status": status}
                    if api_call(create_record, "customers", payload) is not None:
                        st.success("Customer created."); st.rerun()

    search = st.text_input("🔍 Search", key="customer_search")
    if search:
        customers = api_call(list_records, "customers", search=search) or []
        df = as_frame(customers)
    st.metric("Customers", len(customers))
    if df.empty:
        st.info("No customers found.")
        return

    for customer in customers:
        cid = str(customer["id"])
        with st.expander(_customer_label(customer)):
            left, right = st.columns([2, 1])
            with left:
                st.write(f"**Area:** {customer.get('area') or '-'}")
                st.write(f"**Device:** {customer.get('device_type') or '-'}")
                st.write(f"**Status:** {customer.get('status') or '-'}")
                st.write(f"**Address:** {customer.get('address') or '-'}")
                phones = [customer.get(k) for k in ("phone", "phone_1", "phone_2", "phone_3", "phone_4") if customer.get(k)]
                if phones: st.write("**Phones:** " + " · ".join(map(str, phones)))
                if customer.get("location_url"): st.markdown(f"[📍 Open location]({customer['location_url']})")
            with right:
                if st.button("🗑 Delete", key=f"delete_customer_{cid}"):
                    if api_call(delete_record, "customers", cid) is None:
                        st.success("Customer deleted."); st.rerun()
            with st.expander("✏️ Edit"):
                with st.form(f"edit_customer_{cid}"):
                    name = st.text_input("Name", customer.get("name", ""))
                    phone = st.text_input("Phone", customer.get("phone") or "")
                    area = st.text_input("Area", customer.get("area") or "")
                    device = st.text_input("Device type", customer.get("device_type") or "")
                    status = st.selectbox("Status", CUSTOMER_STATUS, index=CUSTOMER_STATUS.index(customer.get("status")) if customer.get("status") in CUSTOMER_STATUS else 0)
                    if st.form_submit_button("Save changes"):
                        payload = {"name": name, "phone": phone or None, "area": area or None, "device_type": device or None, "status": status}
                        if api_call(update_record, "customers", cid, payload) is not None:
                            st.success("Customer updated."); st.rerun()
