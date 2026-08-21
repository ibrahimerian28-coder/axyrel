import streamlit as st
import pandas as pd


def render_customer_summary(customer_visits, row):

    visits_count = len(customer_visits)

    if visits_count > 0:

        last_visit = customer_visits.iloc[0]["visit_date"]

    else:

        last_visit = pd.to_datetime(
            row.get("install_date", ""),
            errors="coerce",
        )

    next_visit = None

    try:

        cycle_months = int(
            float(str(row.get("cycle", "0")).strip())
        )

        if pd.notna(last_visit) and cycle_months > 0:

            next_visit = (
                last_visit
                + pd.DateOffset(months=cycle_months)
            )

    except Exception:

        pass

    days_remaining = None

    if pd.notna(next_visit):

        today = pd.Timestamp.today().normalize()

        days_remaining = (
            next_visit.normalize() - today
        ).days

    visit_status = ""
    visit_icon = ""
    status_message = ""

    if days_remaining is not None:

        if days_remaining < 0:

            visit_status = "Overdue"
            visit_icon = "🔴"
            status_message = (
                f"{abs(days_remaining)} Days Late"
            )

        elif days_remaining <= 30:

            visit_status = "Due Soon"
            visit_icon = "🟡"
            status_message = (
                f"{days_remaining} Days Remaining"
            )

        else:

            visit_status = "On Schedule"
            visit_icon = "🟢"
            status_message = (
                f"{days_remaining} Days Remaining"
            )

    st.subheader("📊 Customer Summary")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "🔧 Total Visits",
            visits_count,
        )

    with col2:

        if pd.notna(last_visit):

            st.metric(
                "📅 Last Visit",
                last_visit.strftime("%Y-%m-%d"),
            )

        else:

            st.metric(
                "📅 Last Visit",
                "-",
            )

    with col3:

        if pd.notna(next_visit):

            st.metric(
                "⏳ Next Visit",
                next_visit.strftime("%Y-%m-%d"),
                status_message,
            )

        else:

            st.metric(
                "⏳ Next Visit",
                "-",
            )

    if visit_status == "On Schedule":

        st.success(
            f"{visit_icon} {visit_status}"
        )

    elif visit_status == "Due Soon":

        st.warning(
            f"{visit_icon} {visit_status}"
        )

    elif visit_status == "Overdue":

        st.error(
            f"{visit_icon} {visit_status}"
        )