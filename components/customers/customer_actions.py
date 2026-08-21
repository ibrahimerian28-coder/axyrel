import streamlit as st
import pandas as pd

from utils.data_service import (
    delete_row_by_uuid,
    update_row,
)


def render_delete_customer(customer_uuid):
    """
    Render customer delete action.
    """

    if st.button(
        "🗑️ Delete",
        key=f"del_{customer_uuid}"
    ):

        st.session_state[
            f"confirm_delete_{customer_uuid}"
        ] = True

    if st.session_state.get(
        f"confirm_delete_{customer_uuid}",
        False
    ):

        st.warning(
            "⚠️ Are you sure you want to delete this customer?"
        )

        col_yes, col_no = st.columns(2)

        with col_yes:

            if st.button(
                "✅ Yes Delete",
                key=f"yes_{customer_uuid}"
            ):

                ok = delete_row_by_uuid(
                    "Customers",
                    customer_uuid
                )

                if ok:

                    st.success("Deleted")

                    del st.session_state[
                        f"confirm_delete_{customer_uuid}"
                    ]

                    st.rerun()

                else:

                    st.error("Delete Failed")

        with col_no:

            if st.button(
                "❌ Cancel",
                key=f"cancel_{customer_uuid}"
            ):

                del st.session_state[
                    f"confirm_delete_{customer_uuid}"
                ]

                st.rerun()
def render_edit_customer(row, customer_uuid, areas, customer_status, device_types):
    """
    Render customer edit form.
    """

    if st.button(
        "✏️ Edit",
        key=f"edit_{customer_uuid}"
    ):

        st.session_state.edit_data = row.to_dict()
        st.session_state.edit_uuid = row.get("uuid")

        st.rerun()

    if (
        "edit_uuid" in st.session_state
        and st.session_state.edit_uuid == row.get("uuid")
    ):

        st.divider()

        st.subheader("✏️ Edit Customer")

        with st.form(f"edit_form_{customer_uuid}"):

            name = st.text_input(
                "Name",
                row.get("name", "")
            )

            phone = st.text_input(
                "Phone",
                row.get("phone", "")
            )

            phone1 = st.text_input(
                "Phone 1",
                row.get("phone_1", "")
            )

            phone2 = st.text_input(
                "Phone 2",
                row.get("phone_2", "")
            )

            phone3 = st.text_input(
                "Phone 3",
                row.get("phone_3", "")
            )

            phone4 = st.text_input(
                "Phone 4",
                row.get("phone_4", "")
            )

            address = st.text_input(
                "Address",
                row.get("address", "")
            )

            current_area = row.get("area", "")

            if current_area not in areas:
                current_area = "Other"

            selected_area = st.selectbox(
                "Area",
                areas,
                index=areas.index(current_area),
                key=f"area_{customer_uuid}"
            )

            custom_area = ""

            if selected_area == "Other":

                custom_area = st.text_input(
                    "Enter New Area",
                    row.get("area", "")
                )

            area = (
                custom_area
                if custom_area
                else selected_area
            )

            location_url = st.text_input(
                "Location URL",
                row.get("location_url", "")
            )

            current_install_date = row.get(
                "install_date",
                ""
            )

            if current_install_date:

                try:

                    current_install_date = pd.to_datetime(
                        current_install_date
                    ).date()

                except (ValueError, TypeError):

                    current_install_date = None

            else:

                current_install_date = None

            install_date = st.date_input(
                "Install Date",
                value=current_install_date
            )

            if install_date:
                install_date = str(install_date)
            else:
                install_date = ""

            cycle = st.text_input(
                "Cycle",
                row.get("cycle", "")
            )

            current_device = row.get(
                "device_type",
                ""
            )

            if current_device not in device_types:
                current_device = "Other"

            selected_device = st.selectbox(
                "Device Type",
                device_types,
                index=device_types.index(current_device),
                key=f"device_{customer_uuid}"
            )

            custom_device = ""

            if selected_device == "Other":

                custom_device = st.text_input(
                    "Enter New Device Type",
                    row.get("device_type", "")
                )

            device_type = (
                custom_device
                if custom_device
                else selected_device
            )

            current_status = row.get(
                "status",
                "Active"
            )

            if current_status not in customer_status:
                current_status = "Active"

            status = st.selectbox(
                "Status",
                customer_status,
                index=customer_status.index(
                    current_status
                ),
                key=f"status_{customer_uuid}"
            )

            save = st.form_submit_button(
                "Save Changes"
            )

            if save:

                updated = {

                    "name": name,

                    "phone": str(phone),
                    "phone_1": str(phone1),
                    "phone_2": str(phone2),
                    "phone_3": str(phone3),
                    "phone_4": str(phone4),

                    "address": address,
                    "area": area,
                    "location_url": location_url,

                    "install_date": install_date,

                    "cycle": cycle,

                    "device_type": device_type,

                    "status": status
                }

                ok = update_row(
                    "Customers",
                    customer_uuid,
                    updated
                )

                if ok:

                    st.success("✅ Updated")

                    if "edit_uuid" in st.session_state:
                        del st.session_state.edit_uuid

                    st.rerun()

                else:

                    st.error("❌ Update Failed")