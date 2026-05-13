"""
kp4.py — Modul KP4 (Kartu Permohonan Penambahan Penghasilan Pegawai)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from modules import sheets_db
from modules.utils import (
    generate_id, now_str, sanitize_input, format_date,
    generate_nomor_surat, status_badge,
)
from modules.auth import require_auth, get_current_user, has_role
from modules.logs import log_activity
from modules.generate_doc import generate_kp4_doc


def _reload():
    sheets_db.get_all_records.clear()


def render():
    require_auth()
    st.markdown("""
    <h1 style="color:#1a237e; font-family:'Plus Jakarta Sans',sans-serif;
        font-weight:800; font-size:1.8rem;">📄 Modul KP4</h1>
    """, unsafe_allow_html=True)

    tabs = ["📋 Daftar KP4", "➕ Buat KP4 Baru"]
    if st.session_state.get("preview_kp4"):
        tabs.append("👁️ Preview Dokumen")
    selected_tabs = st.tabs(tabs)

    with selected_tabs[0]:
        _list_kp4()
    with selected_tabs[1]:
        _form_kp4()
    if st.session_state.get("preview_kp4"):
        with selected_tabs[2]:
            _preview_kp4()


def _list_kp4():
    df = sheets_db.get_dataframe("kp4")
    if df.empty:
        st.info("Belum ada data KP4.")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Cari KP4", key="search_kp4", placeholder="Nama / NIP / Nomor Surat...")
    with col2:
        if "status" in df.columns:
            f_status = st.selectbox("Status", ["Semua"] + sorted(df["status"].dropna().unique().tolist()), key="f_kp4")
        else:
            f_status = "Semua"

    filtered = df.copy()
    if search:
        mask = filtered.astype(str).apply(
            lambda row: row.str.contains(search, case=False, na=False).any(), axis=1
        )
        filtered = filtered[mask]
    if f_status != "Semua" and "status" in filtered.columns:
        filtered = filtered[filtered["status"] == f_status]

    st.markdown(f"<p style='color:#546e7a;'>Menampilkan {len(filtered)} data KP4</p>", unsafe_allow_html=True)

    display_cols = [c for c in ["nomor_surat", "nip", "nama", "tanggal_pengajuan", "perihal", "status"]
                    if c in filtered.columns]
    if display_cols:
        st.dataframe(filtered[display_cols].iloc[::-1].reset_index(drop=True),
                     use_container_width=True, height=400,
                     column_config={
                         "nomor_surat": st.column_config.TextColumn("No. Surat"),
                         "nip": st.column_config.TextColumn("NIP"),
                         "nama": st.column_config.TextColumn("Nama"),
                         "tanggal_pengajuan": st.column_config.TextColumn("Tgl Pengajuan"),
                         "perihal": st.column_config.TextColumn("Perihal"),
                         "status": st.column_config.TextColumn("Status"),
                     })

    # Action
    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        selected_id = st.text_input("ID KP4 untuk Generate/Preview", key="kp4_action_id")
    with col_b:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Generate Dokumen", use_container_width=True):
                if selected_id:
                    found = sheets_db.find_one_by_field("kp4", "id", selected_id.strip())
                    if found:
                        _do_generate_kp4(found)
                    else:
                        st.error("KP4 tidak ditemukan.")
        with c2:
            if st.button("👁️ Preview", use_container_width=True):
                if selected_id:
                    found = sheets_db.find_one_by_field("kp4", "id", selected_id.strip())
                    if found:
                        st.session_state["preview_kp4"] = found
                        st.rerun()


def _form_kp4():
    pegawai_list = sheets_db.get_all_records("pegawai")
    if not pegawai_list:
        st.warning("Tambahkan data pegawai terlebih dahulu.")
        return

    pegawai_options = {f"{p['nama']} ({p['nip']})": p for p in pegawai_list}

    with st.form("form_kp4", clear_on_submit=True):
        st.markdown("#### 📝 Form Pengajuan KP4")

        selected_pegawai = st.selectbox("Pilih Pegawai *", [""] + list(pegawai_options.keys()))

        col1, col2 = st.columns(2)
        with col1:
            tanggal_pengajuan = st.date_input("Tanggal Pengajuan", value=datetime.now())
            perihal = st.text_input("Perihal", value="Permohonan Penambahan Penghasilan Pegawai")
        with col2:
            keterangan = st.text_area("Keterangan")

        submitted = st.form_submit_button("💾 Simpan KP4", use_container_width=True)

        if submitted:
            if not selected_pegawai:
                st.error("Pilih pegawai terlebih dahulu!")
                return

            pegawai = pegawai_options[selected_pegawai]
            kp4_list = sheets_db.get_all_records("kp4")
            nomor = len(kp4_list) + 1
            nomor_surat = generate_nomor_surat("kp4", datetime.now().year, nomor)

            record = {
                "id": generate_id(),
                "pegawai_id": pegawai["id"],
                "nip": pegawai["nip"],
                "nama": pegawai["nama"],
                "tanggal_pengajuan": tanggal_pengajuan.strftime("%Y-%m-%d"),
                "nomor_surat": nomor_surat,
                "perihal": sanitize_input(perihal),
                "keterangan": sanitize_input(keterangan),
                "status": "draft",
                "created_by": get_current_user().get("username", ""),
                "created_at": now_str(),
                "updated_at": now_str(),
            }
            sheets_db.add_record("kp4", record)
            _reload()
            log_activity("buat_kp4", f"Buat KP4: {pegawai['nama']} - {nomor_surat}")
            st.success(f"KP4 berhasil dibuat! Nomor: {nomor_surat}")


def _do_generate_kp4(kp4_data: dict):
    """Generate KP4 document and offer download."""
    pegawai = sheets_db.find_one_by_field("pegawai", "id", kp4_data.get("pegawai_id", ""))
    if not pegawai:
        st.error("Data pegawai tidak ditemukan.")
        return

    doc_data = {**kp4_data, **pegawai}
    try:
        doc_buffer = generate_kp4_doc(doc_data)
        log_activity("generate_kp4", f"Generate dokumen KP4: {kp4_data.get('nama', '-')}")
        st.download_button(
            label="📥 Download KP4 (DOCX)",
            data=doc_buffer,
            file_name=f"KP4_{kp4_data.get('nama', 'doc')}_{datetime.now().strftime('%Y%m%d')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        st.success("Dokumen KP4 berhasil di-generate!")
    except Exception as e:
        st.error(f"Gagal generate dokumen: {e}")


def _preview_kp4():
    kp4 = st.session_state.get("preview_kp4")
    if not kp4:
        st.info("Tidak ada data untuk di-preview.")
        return

    pegawai = sheets_db.find_one_by_field("pegawai", "id", kp4.get("pegawai_id", ""))
    merged = {**(pegawai or {}), **kp4}

    st.markdown("#### 👁️ Preview KP4")
    st.markdown(f"""
    <div style="background:white; padding:2rem; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.08);
        max-width:700px; margin:auto; font-family:'Source Sans 3',sans-serif; line-height:1.8;">

    <div style="text-align:center; margin-bottom:1.5rem;">
        <h3 style="margin:0; color:#1a237e;">KARTU PERMOHONAN PENAMBAHAN PENGHASILAN PEGAWAI</h3>
        <p style="color:#546e7a; font-size:0.9rem;">Nomor: {kp4.get('nomor_surat', '-')}</p>
    </div>

    <table style="width:100%; font-size:0.95rem;">
        <tr><td style="width:180px; font-weight:600;">Nama</td><td>: {merged.get('nama', '-')}</td></tr>
        <tr><td style="font-weight:600;">NIP</td><td>: {merged.get('nip', '-')}</td></tr>
        <tr><td style="font-weight:600;">Golongan</td><td>: {merged.get('golongan', '-')}</td></tr>
        <tr><td style="font-weight:600;">Jabatan</td><td>: {merged.get('jabatan', '-')}</td></tr>
        <tr><td style="font-weight:600;">Unit Kerja</td><td>: {merged.get('unit_kerja', '-')}</td></tr>
        <tr><td style="font-weight:600;">Tgl Pengajuan</td><td>: {format_date(kp4.get('tanggal_pengajuan', ''))}</td></tr>
        <tr><td style="font-weight:600;">Perihal</td><td>: {kp4.get('perihal', '-')}</td></tr>
        <tr><td style="font-weight:600;">Keterangan</td><td>: {kp4.get('keterangan', '-')}</td></tr>
        <tr><td style="font-weight:600;">Status</td><td>: {kp4.get('status', '-')}</td></tr>
    </table>

    <div style="margin-top:2rem; padding-top:1rem; border-top:1px solid #e0e0e0; text-align:center;">
        <p style="color:#90a4ae; font-size:0.8rem;">Preview — Dokumen ini belum ditandatangani</p>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Generate and download
    if st.button("📄 Generate & Download Dokumen", key="prev_kp4_gen"):
        _do_generate_kp4(kp4)

    if st.button("❌ Tutup Preview"):
        del st.session_state["preview_kp4"]
        st.rerun()
