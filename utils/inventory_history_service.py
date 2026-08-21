from datetime import datetime
import uuid

from utils.data_service import add_row


def add_inventory_history(
    movement,
    item_name,
    quantity,
    reference,
    technician,
    notes=""
):

    row = [
        str(uuid.uuid4()),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        movement,
        item_name,
        quantity,
        reference,
        technician,
        notes
    ]

    import streamlit as st
    st.write("History Row:", row)   # ← أضف هذا السطر

    return add_row(
        "Inventory_History",
        row
    )
