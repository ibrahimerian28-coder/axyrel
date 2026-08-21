import streamlit as st
from utils.data_service import (
    load_sheet,
    update_row
)

import pandas as pd
from utils.inventory_history_service import add_inventory_history


def check_inventory(parts_used, inventory_gid):

    df = load_sheet(inventory_gid)

    df.columns = df.columns.str.strip()

    errors = []

    for part in parts_used:

        item = part["item"].strip().lower()
        qty_needed = int(part["qty"])

        match = df[
            df["item_name"]
            .astype(str)
            .str.strip()
            .str.lower()
            == item
        ]

        if match.empty:

            errors.append(
                f"{part['item']} غير موجود بالمخزون."
            )

            continue

        available = pd.to_numeric(
            match.iloc[0]["quantity"],
            errors="coerce"
        )
        
        if pd.isna(available):
            available = 0
        
        available = int(available)

        if available < qty_needed:

            errors.append(
                f"{part['item']} : المتوفر {available} - المطلوب {qty_needed}"
            )

    
    return errors


def deduct_inventory(parts_used, inventory_gid):

    df = load_sheet(inventory_gid)

    df.columns = df.columns.str.strip()

    for part in parts_used:


        item = part["item"].strip().lower()
        qty_used = int(part["qty"])

        match = df[
            df["item_name"]
            .astype(str)
            .str.strip()
            .str.lower()
            == item
        ]

        
        if match.empty:
            continue

        row = match.iloc[0]

        current_qty = pd.to_numeric(
            row["quantity"],
            errors="coerce"
        )
        
        if pd.isna(current_qty):
            current_qty = 0
        
        current_qty = int(current_qty)

        new_qty = current_qty - qty_used

        update_row(
            "Inventory",
            "",
            {
                "item_name": row["item_name"],
                "quantity": new_qty
            }
        )
        add_inventory_history(
            movement="OUT",
            item_name=row["item_name"],
            quantity=qty_used,
            reference="",
            technician="",
            notes="Maintenance Visit"
        )
