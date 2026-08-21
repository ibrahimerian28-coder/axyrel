import streamlit as st


def render_parts_manager(df_inventory):

    st.subheader("🧩 Parts Used")

    used_parts = []

    # =========================
    # STANDARD FILTERS
    # =========================

    st.markdown("### 📦 Standard Filters")

    standard_parts = [
        "P1",
        "P2",
        "P3",
        "Membrane",
        "Post Carbon",
        "Calcite",
        "Infrared"
    ]

    for part in standard_parts:

        col1, col2 = st.columns([3, 1])

        with col1:
            checked = st.checkbox(
                part,
                key=f"chk_{part}"
            )

        qty = 1

        with col2:

            if checked:

                qty = st.number_input(
                    "Qty",
                    min_value=1,
                    value=1,
                    step=1,
                    key=f"qty_{part}",
                    label_visibility="collapsed"
                )

        if checked:

            used_parts.append(
                {
                    "item": part,
                    "qty": qty
                }
            )

    st.divider()

    # =========================
    # OTHER PARTS
    # =========================

    st.markdown("### 🔩 Other Parts")

    excluded = {
        "p1",
        "p2",
        "p3",
        "membrane",
        "post carbon",
        "calcite",
        "infrared"
    }

    inventory_items = []

    if "item_name" in df_inventory.columns:

        inventory_items = (
            df_inventory["item_name"]
            .dropna()
            .astype(str)
            .str.strip()
            .tolist()
        )

        inventory_items = [
            x
            for x in inventory_items
            if x.lower() not in excluded
        ]

    if "other_parts_list" not in st.session_state:

        st.session_state.other_parts_list = []

    c1, c2 = st.columns([3, 1])

    with c1:

        selected = st.selectbox(
            "Part",
            [""] + sorted(inventory_items),
            key="other_part_name"
        )

    with c2:

        qty = st.number_input(
            "Qty",
            min_value=1,
            value=1,
            step=1,
            key="other_part_qty"
        )

    if st.button(
        "➕ Add",
        key="btn_add_other_part"
    ):

        if selected:

            found = False

            for item in st.session_state.other_parts_list:

                if item["item"] == selected:

                    item["qty"] += qty
                    found = True
                    break

            if not found:

                st.session_state.other_parts_list.append(
                    {
                        "item": selected,
                        "qty": qty
                    }
                )

            st.rerun()

    if st.session_state.other_parts_list:

        st.markdown("#### Selected Parts")

        for i, item in enumerate(st.session_state.other_parts_list):

            a, b, c = st.columns([4, 1, 1])

            a.write(item["item"])

            b.write(f"x {item['qty']}")

            if c.button(
                "🗑️",
                key=f"remove_{i}"
            ):

                st.session_state.other_parts_list.pop(i)

                st.rerun()

    used_parts.extend(st.session_state.other_parts_list)
    
    return used_parts
