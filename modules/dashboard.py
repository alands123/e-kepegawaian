"""
dashboard.py — Main Dashboard with Statistics, Charts, and Reminders.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules import sheets_db
from modules.utils import (
    format_currency, kgb_status, days_until_kgb,
    kgb_status_badge, status_badge, format_date, now_str,
)
from modules.auth import get_current_user


def render():
    """Render the main dashboard."""
    user = get_current_user()
    st.markdown(f"""
    <div style="margin-bottom:1.5rem;">
        <h1 style="color:#1a237e; font-family:'Plus Jakarta Sans',sans-serif;
            font-weight:800; font-size:2rem; margin-bottom:4px;">
            Dashboard
        </h1>
        <p style="color:#546e7a; font-size:1rem;">
            Selamat datang, <strong>{user.get('fullname', 'Pengguna')}</strong> —
            {datetime.now().strftime('%A, %d %B %Y')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    df_pegawai = sheets_db.get_dataframe("pegawai")
    df_kgb = sheets_db.get_dataframe("kgb")
    df_kp4 = sheets_db.get_dataframe("kp4")
    df_logs = sheets_db.get_dataframe("logs")

    # -----------------------------------------------------------------------
    # Stat Cards
    # -----------------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    total_pegawai = len(df_pegawai)
    total_pns = len(df_pegawai[df_pegawai.get("status", pd.Series()) == "PNS"]) if "status" in df_pegawai.columns else 0
    total_cpns = len(df_pegawai[df_pegawai.get("status", pd.Series()) == "CPNS"]) if "status" in df_pegawai.columns else 0
    total_kgb = len(df_kgb)

    with col1:
        st.metric("👤 Total Pegawai", total_pegawai)
    with col2:
        st.metric("📋 PNS", total_pns)
    with col3:
        st.metric("📝 CPNS", total_cpns)
    with col4:
        st.metric("📊 Total KGB", total_kgb)

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # KGB Reminder Section
    # -----------------------------------------------------------------------
    st.markdown("### 🔔 Monitoring KGB Mendatang")
    if not df_kgb.empty and "jatuh_tempo" in df_kgb.columns:
        df_kgb["days_left"] = df_kgb["jatuh_tempo"].apply(days_until_kgb)
        df_kgb["stat"] = df_kgb["jatuh_tempo"].apply(kgb_status)

        urgent = df_kgb[df_kgb["days_left"].between(-365, 90)].sort_values("days_left")

        if not urgent.empty:
            for _, row in urgent.head(8).iterrows():
                badge = kgb_status_badge(row["stat"])
                days = row["days_left"]
                days_text = f"terlambat {abs(days)} hari" if days < 0 else f"{days} hari lagi"
                st.markdown(f"""
                <div style="background:white; padding:12px 16px; border-radius:8px;
                    margin-bottom:8px; border-left:4px solid
                    {'#c62828' if days < 0 else '#ef6c00' if days <= 30 else '#0277bd'};
                    box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                    <strong>{row.get('nama', '-')}</strong>
                    &nbsp;{badge}&nbsp;
                    <span style="color:#546e7a; font-size:0.85rem;">
                    Jatuh tempo: {format_date(row.get('jatuh_tempo', ''))} ({days_text})
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Tidak ada KGB yang mendekati jatuh tempo dalam 90 hari ke depan.")
    else:
        st.info("Belum ada data KGB.")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Charts
    # -----------------------------------------------------------------------
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("#### 📊 Distribusi Golongan")
        if not df_pegawai.empty and "golongan" in df_pegawai.columns:
            gol_counts = df_pegawai["golongan"].value_counts().reset_index()
            gol_counts.columns = ["Golongan", "Jumlah"]
            fig = px.bar(
                gol_counts, x="Golongan", y="Jumlah",
                color_discrete_sequence=["#1a237e"],
                template="plotly_white",
            )
            fig.update_layout(
                margin=dict(t=10, b=10),
                height=300,
                font=dict(family="Plus Jakarta Sans"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data pegawai.")

    with col_chart2:
        st.markdown("#### 📈 Status Pegawai")
        if not df_pegawai.empty and "status" in df_pegawai.columns:
            stat_counts = df_pegawai["status"].value_counts().reset_index()
            stat_counts.columns = ["Status", "Jumlah"]
            fig2 = px.pie(
                stat_counts, names="Status", values="Jumlah",
                color_discrete_sequence=["#1a237e", "#ffc107", "#2e7d32", "#ef6c00", "#90a4ae"],
                template="plotly_white",
            )
            fig2.update_layout(
                margin=dict(t=10, b=10),
                height=300,
                font=dict(family="Plus Jakarta Sans"),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Belum ada data pegawai.")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Recent Activity
    # -----------------------------------------------------------------------
    col_log, col_quick = st.columns([2, 1])

    with col_log:
        st.markdown("#### 📝 Aktivitas Terbaru")
        if not df_logs.empty:
            recent = df_logs.tail(10).iloc[::-1]
            for _, log in recent.iterrows():
                st.markdown(f"""
                <div style="padding:8px 12px; border-bottom:1px solid #eee; font-size:0.85rem;">
                    <span style="color:#1a237e; font-weight:600;">{log.get('user', '-')}</span>
                    &nbsp;·&nbsp; {log.get('action', '-')}
                    &nbsp;·&nbsp; <span style="color:#90a4ae;">{log.get('timestamp', '-')}</span>
                    <br><span style="color:#546e7a;">{log.get('details', '')}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Belum ada aktivitas.")

    with col_quick:
        st.markdown("#### ⚡ Aksi Cepat")
        if st.button("➕ Tambah Pegawai", use_container_width=True):
            st.session_state["nav_action"] = "tambah_pegawai"
            st.rerun()
        if st.button("📄 Buat KP4 Baru", use_container_width=True):
            st.session_state["nav_action"] = "buat_kp4"
            st.rerun()
        if st.button("📊 Buat KGB Baru", use_container_width=True):
            st.session_state["nav_action"] = "buat_kgb"
            st.rerun()
        if st.button("📥 Export Laporan", use_container_width=True):
            st.session_state["nav_action"] = "export"
            st.rerun()
