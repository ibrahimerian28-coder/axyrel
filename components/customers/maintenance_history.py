import json
import pandas as pd
import streamlit as st


def render_customer_maintenance_history(customer_visits):

    st.subheader("🛠 سجل الصيانات")

    if customer_visits.empty:

        st.info("لا توجد زيارات صيانة")

        return

    customer_visits = customer_visits.sort_values(
        "visit_date",
        ascending=False
    )

    for _, visit in customer_visits.iterrows():

        visit_date = ""

        if pd.notna(visit["visit_date"]):

            visit_date = visit["visit_date"].strftime("%Y-%m-%d")

        with st.container(border=True):

            col1, col2, col3 = st.columns(3)

            with col1:

                st.markdown("**📅 التاريخ**")
                st.write(visit_date)

            with col2:

                st.markdown("**👨‍🔧 الفني**")
                st.write(
                    visit.get("technician", "-")
                )

            with col3:

                st.markdown("**💰 التكلفة**")
                st.write(
                    f"{visit.get('amount', 0)} ج.م"
                )

            st.markdown("### 🧩 قطع الغيار المستخدمة")

            used_parts = []

            try:

                if pd.notna(
                    visit.get("used_parts")
                ):

                    used_parts = json.loads(
                        visit["used_parts"]
                    )

            except Exception:

                used_parts = []

            if used_parts:

                parts_table = pd.DataFrame(
                    used_parts
                )

                parts_table.columns = [
                    "Part",
                    "Qty",
                ]

                st.dataframe(
                    parts_table,
                    hide_index=True,
                    use_container_width=True,
                )

            else:

                st.info(
                    "لم يتم استخدام قطع غيار"
                )

            if str(
                visit.get("notes", "")
            ).strip():

                st.markdown("### 📝 ملاحظات")

                st.write(
                    visit["notes"]
                )

            st.divider()