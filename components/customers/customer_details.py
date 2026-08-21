import streamlit as st


def render_customer_details(row):
    """
    Render customer details block.
    """

    st.subheader("📋 Customer Details")

    # Address
    # Address
    if row.get("address"):
        st.write(f"🏠 {row.get('address')}")

    # Install date
    if row.get("install_date"):
        st.write(f"📅 {row.get('install_date')}")

    # Cycle
    if row.get("cycle"):
        st.write(f"🔁 Cycle: {row.get('cycle')}")

    # Status
    status = str(row.get("status", "")).strip()

    if status == "Active":
        st.success("🟢 Active")

    elif status == "Inactive":
        st.error("🔴 Inactive")

    elif status:
        st.info(status)

    # Location
    loc = str(row.get("location_url", "")).strip()

    if loc and loc.lower() != "nan":
        st.markdown(f"[📍 Open Location]({loc})")