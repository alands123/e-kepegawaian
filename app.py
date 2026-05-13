"""
app.py — e-Kepegawaian: Sistem Arsip & Manajemen Data Kepegawaian
Main entry point for Streamlit application.
"""

import streamlit as st
import sys
import os

# Ensure modules are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules import sheets_db
from modules import auth
from modules import dashboard
from modules import pegawai
from modules import kp4
from modules import kgb
from modules import export_data
from modules import logs
from modules import notifications
from modules import backup
from modules import settings

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="e-Kepegawaian",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Load Custom CSS
# ---------------------------------------------------------------------------
css_path = os.path.join(os.path.dirname(__file__), "assets", "css", "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Initialize Database Sheets
# ---------------------------------------------------------------------------
try:
    sheets_db.init_all_sheets()
    auth.init_default_admin()
except Exception as e:
    st.error(f"Gagal inisialisasi database: {e}")
    st.info(
        "Pastikan Google Sheets API sudah dikonfigurasi dengan benar dan "
        "spreadsheet sudah di-share ke service account."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Authentication Gate
# ---------------------------------------------------------------------------
if not auth.is_authenticated():
    auth.render_login_page()
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
from streamlit_option_menu import option_menu

user = auth.get_current_user()
role = user.get("role", "viewer")

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:1rem 0 0.5rem 0;">
        <div style="font-size:2.2rem;">🏛️</div>
        <h2 style="color:white; margin:4px 0; font-family:'Plus Jakarta Sans',sans-serif;
            font-weight:800; font-size:1.3rem;">e-Kepegawaian</h2>
        <p style="color:#8c9eff; font-size:0.75rem; margin:0;">Sistem Arsip & Data Kepegawaian</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Menu items based on role
    menu_items = ["Dashboard", "Pegawai", "KP4", "KGB"]
    menu_icons = ["speedometer2", "people", "file-earmark-text", "graph-up"]

    if role in ("admin", "operator"):
        menu_items.extend(["Export Laporan"])
        menu_icons.extend(["download"])

    menu_items.extend(["Notifikasi", "Audit Log"])
    menu_icons.extend(["bell", "journal-text"])

    if role == "admin":
        menu_items.extend(["Backup & Restore", "Pengaturan"])
        menu_icons.extend(["cloud-arrow-down", "gear"])

    selected = option_menu(
        menu_title=None,
        options=menu_items,
        icons=menu_icons,
        menu_icon="list",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#8c9eff", "font-size": "16px"},
            "nav-link": {
                "font-size": "14px",
                "font-family": "'Plus Jakarta Sans', sans-serif",
                "font-weight": "500",
                "color": "#c5cae9",
                "padding": "10px 14px",
                "border-radius": "8px",
                "margin": "2px 0",
                "--hover-color": "#1a237e",
            },
            "nav-link-selected": {
                "background-color": "#ffc107",
                "color": "#1a237e",
                "font-weight": "700",
            },
        },
    )

    st.markdown("---")

    # User info
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.08); padding:12px; border-radius:10px;
        margin-top:auto;">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="background:#ffc107; color:#1a237e; width:36px; height:36px;
                border-radius:50%; display:flex; align-items:center; justify-content:center;
                font-weight:800; font-size:0.9rem;">
                {user.get('fullname', 'U')[0].upper()}
            </div>
            <div>
                <div style="color:white; font-weight:600; font-size:0.85rem;">
                    {user.get('fullname', 'User')}
                </div>
                <div style="color:#8c9eff; font-size:0.7rem; text-transform:uppercase;">
                    {role}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout", use_container_width=True):
        from modules.logs import log_activity
        log_activity("logout", f"User {user.get('username', '')} logout")
        auth.logout_user()
        st.rerun()

# ---------------------------------------------------------------------------
# Handle Navigation Actions (from Dashboard quick actions)
# ---------------------------------------------------------------------------
nav_action = st.session_state.pop("nav_action", None)
if nav_action == "tambah_pegawai":
    selected = "Pegawai"
elif nav_action in ("buat_kp4",):
    selected = "KP4"
elif nav_action in ("buat_kgb",):
    selected = "KGB"
elif nav_action == "export":
    selected = "Export Laporan"

# ---------------------------------------------------------------------------
# Route to Selected Page
# ---------------------------------------------------------------------------
if selected == "Dashboard":
    dashboard.render()
elif selected == "Pegawai":
    pegawai.render()
elif selected == "KP4":
    kp4.render()
elif selected == "KGB":
    kgb.render()
elif selected == "Export Laporan":
    export_data.render()
elif selected == "Notifikasi":
    notifications.render()
elif selected == "Audit Log":
    logs.render()
elif selected == "Backup & Restore":
    backup.render()
elif selected == "Pengaturan":
    settings.render()
