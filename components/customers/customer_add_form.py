import streamlit as st
import uuid

from utils.data_service import add_row
from utils.constants import (
    AREAS,
    CUSTOMER_STATUS,
    DEVICE_TYPES
)
def render_add_customer():
    with st.expander("➕ Add Customer"):
    
            with st.container():
    
                with st.form("add_customer"):
        
                    name = st.text_input("Name")
        
                    phone = st.text_input("Phone", value="", help="Keep leading zero")
                    phone1 = st.text_input("Phone 1", value="", help="Keep leading zero")
                    phone2 = st.text_input("Phone 2", value="", help="Keep leading zero")
                    phone3 = st.text_input("Phone 3", value="", help="Keep leading zero")
                    phone4 = st.text_input("Phone 4", value="", help="Keep leading zero")
        
                    address = st.text_input("Address")
                    selected_area = st.selectbox(
                        "Area",
                        AREAS
                    )
        
                    custom_area = ""
        
                    if selected_area == "Other":
        
                        custom_area = st.text_input(
                        "Enter New Area"
                        )
        
                    area = custom_area if custom_area else selected_area
        
                    location_url = st.text_input("Google Maps URL")
        
                    install_date = st.date_input(
                        "Install Date",
                        value=None
                    )
        
                    if install_date:
                        install_date = str(install_date)
                    else:
                        install_date = ""
                    cycle = st.text_input("Cycle")
                    selected_device = st.selectbox(
                        "Device Type",
                        DEVICE_TYPES
                    )
        
                    custom_device = ""
        
                    if selected_device == "Other":
        
                        custom_device = st.text_input(
                            "Enter New Device Type"
                        )
        
                    device_type = (
                        custom_device
                        if custom_device
                        else selected_device
                    )
        
                    status = st.selectbox(
                        "Status",
                        CUSTOMER_STATUS,
                        index=0
                    )
        
                    submit = st.form_submit_button("Save")
        
                    if submit:
        
                        customer_uuid = str(uuid.uuid4())
        
                        new_row = [
                            name,
                            "",
                            "",
                            customer_uuid,
        
                            str(phone),
                            str(phone1),
                            str(phone2),
                            str(phone3),
                            str(phone4),
        
                            address,
                            area,
                            location_url,
        
                            install_date,
                            cycle,
                            device_type,
                            status
                        ]
        
                        ok = add_row("Customers", new_row)
        
                        if ok:
        
                            st.success("✅ Customer Added")
        
                            st.rerun()
        
                        else:
        
                            st.error("❌ Failed")