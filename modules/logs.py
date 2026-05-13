"""
logs.py — Audit Log System
"""

import streamlit as st
from modules import sheets_db
from modules.utils import generate_id, now_str
from modules.auth import get_current_user


def log_activity(action: str, details: str = ""):
    """Record an audit log entry."""
    user = get_current_user()
    record = {
        "id": generate_id(),
        "user": user.get("username", "system"),
        "action": action,
        "details": details,
        "timestamp": now_str(),
    }
    try:
        sheets_db.add_record("logs", record)
    except Exception:
        pass  # Non-blocking


def render():
    st.markdown("""
    <h1 style="color:#1a237e; font-family:'Plus Jakarta Sans',sans-serif;
        font-weight:800; font-size:1.8rem;">📋 Audit Log</h1>
    """, unsafe_allow_html=True)

    df = sheets_db.get_dataframe("logs")
    if df.empty:
        st.info("Belum ada log aktivitas.")
        return

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        search = st.text_input("🔍 Cari log", placeholder="User / Aksi / Detail...")
    with col2:
        if "action" in df.columns:
            f_action = st.selectbox("Aksi", ["Semua"] + sorted(df["action"].dropna().unique().tolist()))
        else:
            f_action = "Semua"

    filtered = df.copy()
    if search:
        mask = filtered.astype(str).apply(
            lambda row: row.str.contains(search, case=False, na=False).any(), axis=1
        )
        filtered = filtered[mask]
    if f_action != "Semua" and "action" in filtered.columns:
        filtered = filtered[filtered["action"] == f_action]

    st.markdown(f"<p style='color:#546e7a;'>Menampilkan {len(filtered)} log</p>",
                unsafe_allow_html=True)

    # Display
    for _, log in filtered.tail(50).iloc[::-1].iterrows():
        st.markdown(f"""
        <div style="padding:10px 14px; border-bottom:1px solid #eee; font-size:0.85rem;">
            <span style="background:#e8eaf6; padding:2px 8px; border-radius:4px; font-weight:600;
                color:#1a237e; font-size:0.8rem;">{log.get('user', '-')}</span>
            &nbsp; <strong>{log.get('action', '-')}</strong>
            &nbsp; <span style="color:#90a4ae;">{log.get('timestamp', '-')}</span>
            <br><span style="color:#546e7a;">{log.get('details', '')}</span>
        </div>
        """, unsafe_allow_html=True)
