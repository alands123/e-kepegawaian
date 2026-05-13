"""
notifications.py — Notification & Reminder System
"""

import streamlit as st
from datetime import datetime
from modules import sheets_db
from modules.utils import generate_id, now_str, days_until_kgb, format_date
from modules.auth import get_current_user


def create_notification(user_id: str, title: str, message: str, notif_type: str = "info"):
    record = {
        "id": generate_id(),
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notif_type,
        "is_read": "0",
        "created_at": now_str(),
    }
    sheets_db.add_record("notifications", record)


def get_user_notifications(user_id: str) -> list[dict]:
    records = sheets_db.get_all_records("notifications")
    return [r for r in records if r.get("user_id") == user_id]


def mark_as_read(notif_id: str):
    sheets_db.update_record("notifications", notif_id, {"is_read": "1"})


def check_kgb_reminders():
    """Check for KGB due dates and create notifications."""
    kgb_list = sheets_db.get_all_records("kgb")
    users = sheets_db.get_all_records("users")
    admin_users = [u for u in users if u.get("role") in ("admin", "operator")]

    for kgb in kgb_list:
        days = days_until_kgb(kgb.get("jatuh_tempo", ""))
        nama = kgb.get("nama", "-")

        if days == 30 or days == 7 or days == 0 or days < 0:
            for user in admin_users:
                existing = [
                    n for n in get_user_notifications(user["id"])
                    if kgb.get("id", "") in n.get("message", "") and str(days) in n.get("message", "")
                ]
                if not existing:
                    if days < 0:
                        title = f"KGB Terlambat: {nama}"
                        msg = f"KGB {nama} terlambat {abs(days)} hari. ID: {kgb.get('id', '')}"
                        notif_type = "danger"
                    elif days == 0:
                        title = f"KGB Jatuh Tempo Hari Ini: {nama}"
                        msg = f"KGB {nama} jatuh tempo hari ini! ID: {kgb.get('id', '')}"
                        notif_type = "warning"
                    else:
                        title = f"KGB Mendekati Jatuh Tempo: {nama}"
                        msg = f"KGB {nama} jatuh tempo {days} hari lagi. ID: {kgb.get('id', '')}"
                        notif_type = "info"
                    create_notification(user["id"], title, msg, notif_type)


def render():
    st.markdown("""
    <h1 style="color:#1a237e; font-family:'Plus Jakarta Sans',sans-serif;
        font-weight:800; font-size:1.8rem;">🔔 Notifikasi</h1>
    """, unsafe_allow_html=True)

    user = get_current_user()
    if not user:
        return

    # Check KGB reminders
    check_kgb_reminders()

    notifs = get_user_notifications(user.get("id", ""))
    if not notifs:
        st.info("Tidak ada notifikasi.")
        return

    unread = [n for n in notifs if str(n.get("is_read", "0")) == "0"]
    st.markdown(f"<p style='color:#546e7a;'>{len(unread)} notifikasi belum dibaca</p>",
                unsafe_allow_html=True)

    for notif in sorted(notifs, key=lambda x: x.get("created_at", ""), reverse=True)[:30]:
        is_read = str(notif.get("is_read", "0")) == "1"
        icon = "📧" if not is_read else "📭"
        bg = "#e3f2fd" if not is_read else "#ffffff"
        border = "#0277bd" if not is_read else "#e0e0e0"
        ntype = notif.get("type", "info")
        icon_type = {"danger": "🔴", "warning": "🟡", "info": "🔵", "success": "🟢"}.get(ntype, "🔵")

        st.markdown(f"""
        <div style="background:{bg}; padding:12px 16px; border-radius:8px;
            margin-bottom:6px; border-left:4px solid {border};
            {'font-weight:500;' if not is_read else ''}">
            {icon} {icon_type} <strong>{notif.get('title', '-')}</strong>
            <br><span style="color:#546e7a; font-size:0.85rem;">{notif.get('message', '')}</span>
            <br><span style="color:#90a4ae; font-size:0.75rem;">{notif.get('created_at', '')}</span>
        </div>
        """, unsafe_allow_html=True)

        if not is_read:
            if st.button(f"Tandai dibaca", key=f"read_{notif['id']}"):
                mark_as_read(notif["id"])
                st.rerun()
