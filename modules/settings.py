"""
settings.py — System Settings & User Management
"""

import streamlit as st
from modules import sheets_db
from modules.auth import (
    require_role, create_user, update_user, get_current_user, has_role
)
from modules.utils import now_str, generate_id
from modules.logs import log_activity


def render():
    require_role(["admin"])
    st.markdown("""
    <h1 style="color:#1a237e; font-family:'Plus Jakarta Sans',sans-serif;
        font-weight:800; font-size:1.8rem;">⚙️ Pengaturan Sistem</h1>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["👥 Manajemen User", "🔧 Pengaturan Umum", "📄 Template Dokumen"])

    with tabs[0]:
        _user_management()
    with tabs[1]:
        _general_settings()
    with tabs[2]:
        _template_settings()


def _user_management():
    st.markdown("#### 👥 Manajemen Pengguna")

    # List users
    users = sheets_db.get_all_records("users")
    if users:
        import pandas as pd  # noqa: E401
        df = pd.DataFrame(users)
        display_cols = [c for c in ["username", "fullname", "role", "email", "active", "last_login"]
                        if c in df.columns]
        if display_cols:
            st.dataframe(df[display_cols], use_container_width=True)

    st.markdown("---")

    # Add user
    st.markdown("##### ➕ Tambah User Baru")
    with st.form("form_add_user", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username *")
            fullname = st.text_input("Nama Lengkap *")
        with col2:
            password = st.text_input("Password *", type="password")
            role = st.selectbox("Role", ["admin", "operator", "viewer"])

        email = st.text_input("Email")
        phone = st.text_input("Telepon")

        if st.form_submit_button("💾 Simpan User", use_container_width=True):
            if not username or not password or not fullname:
                st.error("Username, Password, dan Nama Lengkap wajib diisi!")
            else:
                try:
                    create_user(username.strip(), password, fullname.strip(), role, email, phone)
                    log_activity("tambah_user", f"Tambah user: {username}")
                    st.success(f"User '{username}' berhasil dibuat!")
                except ValueError as e:
                    st.error(str(e))

    st.markdown("---")

    # Edit user
    st.markdown("##### ✏️ Edit User")
    usernames = [u["username"] for u in users] if users else []
    if usernames:
        selected = st.selectbox("Pilih user", [""] + usernames, key="edit_user_sel")
        if selected:
            user = next((u for u in users if u["username"] == selected), None)
            if user:
                with st.form("form_edit_user"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_fullname = st.text_input("Nama Lengkap", value=user.get("fullname", ""))
                        new_role = st.selectbox("Role", ["admin", "operator", "viewer"],
                                                index=["admin", "operator", "viewer"].index(user.get("role", "viewer")))
                    with col2:
                        new_email = st.text_input("Email", value=user.get("email", ""))
                        new_active = st.checkbox("Aktif", value=str(user.get("active", "1")) in ("1", "True", "true"))
                    new_password = st.text_input("Password Baru (kosongkan jika tidak diubah)", type="password")

                    if st.form_submit_button("💾 Update User"):
                        updates = {
                            "fullname": new_fullname,
                            "role": new_role,
                            "email": new_email,
                            "active": "1" if new_active else "0",
                        }
                        if new_password:
                            updates["password"] = new_password
                        from modules.auth import update_user
                        update_user(user["id"], updates)
                        sheets_db.get_all_records.clear()
                        log_activity("edit_user", f"Edit user: {selected}")
                        st.success(f"User '{selected}' berhasil diupdate!")
                        st.rerun()


def _general_settings():
    st.markdown("#### 🔧 Pengaturan Umum")

    # Nama instansi
    instansi = sheets_db.get_setting("nama_instansi", "Dinas Pendidikan Provinsi ...")
    alamat = sheets_db.get_setting("alamat_instansi", "Jl. ........")
    telepon = sheets_db.get_setting("telepon_instansi", "")
    nama_kepala = sheets_db.get_setting("nama_kepala_dinas", "")
    nip_kepala = sheets_db.get_setting("nip_kepala_dinas", "")

    with st.form("form_settings"):
        new_instansi = st.text_input("Nama Instansi", value=instansi)
        new_alamat = st.text_input("Alamat Instansi", value=alamat)
        new_telepon = st.text_input("Telepon Instansi", value=telepon)
        new_nama_kepala = st.text_input("Nama Kepala Dinas", value=nama_kepala)
        new_nip_kepala = st.text_input("NIP Kepala Dinas", value=nip_kepala)

        if st.form_submit_button("💾 Simpan Pengaturan"):
            sheets_db.set_setting("nama_instansi", new_instansi)
            sheets_db.set_setting("alamat_instansi", new_alamat)
            sheets_db.set_setting("telepon_instansi", new_telepon)
            sheets_db.set_setting("nama_kepala_dinas", new_nama_kepala)
            sheets_db.set_setting("nip_kepala_dinas", new_nip_kepala)
            log_activity("update_settings", "Update pengaturan umum")
            st.success("Pengaturan berhasil disimpan!")


def _template_settings():
    st.markdown("#### 📄 Manajemen Template Dokumen")
    st.info("Kelola template dokumen KP4 dan KGB. Template disimpan di database.")

    # Show current templates
    templates = sheets_db.get_all_records("settings")
    kp4_tpl = sheets_db.get_setting("template_kp4_active", "default")
    kgb_tpl = sheets_db.get_setting("template_kgb_active", "default")

    st.markdown(f"""
    | Template | Status |
    |---|---|
    | Template KP4 | {'Default (built-in)' if kp4_tpl == 'default' else kp4_tpl} |
    | Template KGB | {'Default (built-in)' if kgb_tpl == 'default' else kgb_tpl} |
    """)

    st.markdown("---")
    st.markdown("##### 📤 Upload Template Custom")

    tpl_type = st.selectbox("Jenis Template", ["KP4", "KGB"])
    tpl_file = st.file_uploader("Upload file DOCX template", type=["docx"])

    if tpl_file and st.button("💾 Simpan Template"):
        import base64
        content = base64.b64encode(tpl_file.read()).decode("utf-8")
        sheets_db.set_setting(f"template_{tpl_type.lower()}_data", content)
        sheets_db.set_setting(f"template_{tpl_type.lower()}_active", "custom")
        log_activity("upload_template", f"Upload template {tpl_type}")
        st.success(f"Template {tpl_type} berhasil disimpan!")

    if st.button("🔄 Reset ke Template Default"):
        sheets_db.set_setting(f"template_{tpl_type.lower()}_active", "default")
        sheets_db.set_setting(f"template_{tpl_type.lower()}_data", "")
        st.success(f"Template {tpl_type} di-reset ke default.")
