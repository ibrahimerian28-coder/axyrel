from __future__ import annotations

import streamlit as st

from backend.core.config import settings
from utils.api_client import APIClientError, login as api_login, logout as api_logout
from utils.config import LOGO_PATH
from utils.router import route

st.set_page_config(page_title="Axyrel", page_icon="🚰", layout="wide")

st.markdown("""
<style>
section[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebar"] { overflow-y: auto !important; height: 100vh; }
</style>
""", unsafe_allow_html=True)

if "user_type" not in st.session_state:
    st.session_state.user_type = None
if "api_user" not in st.session_state:
    st.session_state.api_user = None

if not settings.ui_api_enabled:
    st.error("Axyrel API mode is disabled. Set AXYREL_UI_API_ENABLED=true in .env, restart Streamlit, and try again.")
    st.stop()

if st.session_state.user_type is None:
    st.title("🚰 Axyrel")
    st.caption("Enterprise Field Service Operating Platform")
    with st.form("login"):
        email = st.text_input("Email", value="admin@axyrel.local")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
    if submitted:
        try:
            user = api_login(email, password)
            st.session_state.api_user = user
            st.session_state.user_type = str(user.get("role", "")).lower()
            st.rerun()
        except APIClientError as exc:
            st.error(str(exc))
    st.info("Customer self-service login is not enabled in the current MVP API; team authentication is the supported entry point.")
    st.stop()

user = st.session_state.api_user or {}
role = str(user.get("role", "")).lower()
permissions = set(user.get("permissions", []))

st.sidebar.image(LOGO_PATH, width=150)
st.sidebar.success("API Mode: FastAPI + PostgreSQL")
st.sidebar.caption(f"{user.get('full_name', 'User')} · {role.title()}")
if st.sidebar.button("Logout", use_container_width=True):
    api_logout()
    st.session_state.user_type = None
    st.rerun()

menu_by_permission = [
    ("Dashboard", "report:read"),
    ("Customers", "customer:read"),
    ("Maintenance", "service:read"),
    ("Inventory", "inventory:read"),
    ("Expenses", "expense:read"),
    ("Invoices", "billing:read"),
    ("Profitability", "report:read"),
]
menu = [name for name, perm in menu_by_permission if perm in permissions]
if role == "admin":
    menu.append("Store")
if not menu:
    st.error("Your account has no available modules.")
    st.stop()

page = st.sidebar.radio("Modules", menu)
route(page)
