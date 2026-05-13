"""
kgb.py — Modul KGB (Kenaikan Gaji Berkala) + Monitoring
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from modules import sheets_db
from modules.utils import (
    generate_id, now_str, sanitize_input, format_date,
    format_currency, generate_nomor_surat, status_badge,
    calculate_jatuh_tempo, days_until_kgb, kgb_status,
    kgb_status_badge, GOLONGAN_LIST,
)
from modules.auth import require_auth, get_current_user
from modules.logs import log_activity
from modules.generate_doc import generate_kgb_doc


def _reload():
    sheets_db.get_all_records.clear()


def render():
    require_auth()
    st.markdown("""
    <h1 style="color:#1a237e; font-family:'Plus Jakarta Sans',sans-serif;
        font-weight:800; font-size:1.8rem;">📊 Modul KGB</h1>
    """, unsafe_allow_html=True)

    tabs = ["📋 Daftar KGB", "➕ Buat KGB Baru", "🔔 Monitoring Jatuh Tempo"]
    if st.session_state.get("preview_kgb"):
        tabs.append("👁️ Preview Dokumen")
    selected_tabs = st.tabs(tabs)

    with selected_tabs[0]:
        _list_kgb()
    with selected_tabs[1]:
        _form_kgb()
    with selected_tabs[2]:
        _monitor_kgb()
    if st.session_state.get("preview_kgb"):
        idx = 3
        with selected_tabs[idx]:
            _preview_kgb()


def _list_kgb():
    df = sheets_db.get_dataframe("kgb")
    if df.empty:
        st.info("Belum ada data KGB.")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Cari KGB", key="search_kgb", placeholder="Nama / NIP / No. Surat...")
    with col2:
        f_status = st.selectbox("Status", ["Semua", "draft", "diajukan", "disetujui", "selesai"], key="f_kgb")

    filtered = df.copy()
    if search:
        mask = filtered.astype(str).apply(
            lambda row: row.str.contains(search, case=False, na=False).any(), axis=1
        )
        filtered = filtered[mask]
    if f_status != "Semua" and "status" in filtered.columns:
        filtered = filtered[filtered["status"] == f_status]

    st.markdown(f"<p style='color:#546e7a;'>Menampilkan {len(filtered)} data KGB</p>", unsafe_allow_html=True)

    display_cols = [c for c in ["nomor_surat", "nip", "nama", "golongan", "jatuh_tempo", "gaji_lama", "gaji_baru", "status"]
                    if c in filtered.columns]
    if display_cols:
        st.dataframe(filtered[display_cols].iloc[::-1].reset_index(drop=True),
                     use_container_width=True, height=400,
                     column_config={
                         "nomor_surat": st.column_config.TextColumn("No. Surat"),
                         "nip": st.column_config.TextColumn("NIP"),
                         "nama": st.column_config.TextColumn("Nama"),
                         "golongan": st.column_config.TextColumn("Gol."),
                         "jatuh_tempo": st.column_config.TextColumn("Jatuh Tempo"),
                         "gaji_lama": st.column_config.TextColumn("Gaji Lama"),
                         "gaji_baru": st.column_config.TextColumn("Gaji Baru"),
                         "status": st.column_config.TextColumn("Status"),
                     })

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        selected_id = st.text_input("ID KGB untuk Generate/Preview", key="kgb_action_id")
    with col_b:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Generate Dokumen", use_container_width=True):
                if selected_id:
                    found = sheets_db.find_one_by_field("kgb", "id", selected_id.strip())
                    if found:
                        _do_generate_kgb(found)
                    else:
                        st.error("Data KGB tidak ditemukan.")
        with c2:
            if st.button("👁️ Preview", use_container_width=True):
                if selected_id:
                    found = sheets_db.find_one_by_field("kgb", "id", selected_id.strip())
                    if found:
                        st.session_state["preview_kgb"] = found
                        st.rerun()


def _form_kgb():
    pegawai_list = sheets_db.get_all_records("pegawai")
    if not pegawai_list:
        st.warning("Tambahkan data pegawai terlebih dahulu.")
        return

    pegawai_options = {f"{p['nama']} ({p['nip']})": p for p in pegawai_list}

    with st.form("form_kgb", clear_on_submit=True):
        st.markdown("#### 📝 Form Pengajuan KGB")

        selected = st.selectbox("Pilih Pegawai *", [""] + list(pegawai_options.keys()))

        col1, col2 = st.columns(2)
        with col1:
            tanggal_pengajuan = st.date_input("Tanggal Pengajuan", value=datetime.now())
            gaji_lama = st.number_input("Gaji Lama (Rp)", min_value=0, step=100000)
        with col2:
            gaji_baru = st.number_input("Gaji Baru (Rp)", min_value=0, step=100000)
            keterangan = st.text_area("Keterangan")

        submitted = st.form_submit_button("💾 Simpan KGB", use_container_width=True)

        if submitted:
            if not selected:
                st.error("Pilih pegawai!")
                return

            pegawai = pegawai_options[selected]
            tmt = pegawai.get("tmt_golongan", "")
            jatuh_tempo = calculate_jatuh_tempo(tmt)

            kgb_list = sheets_db.get_all_records("kgb")
            nomor = len(kgb_list) + 1
            nomor_surat = generate_nomor_surat("kgb", datetime.now().year, nomor)

            record = {
                "id": generate_id(),
                "pegawai_id": pegawai["id"],
                "nip": pegawai["nip"],
                "nama": pegawai["nama"],
                "golongan": pegawai.get("golongan", ""),
                "tmt_golongan": tmt,
                "jatuh_tempo": jatuh_tempo,
                "gaji_lama": str(gaji_lama),
                "gaji_baru": str(gaji_baru),
                "tanggal_pengajuan": tanggal_pengajuan.strftime("%Y-%m-%d"),
                "nomor_surat": nomor_surat,
                "keterangan": sanitize_input(keterangan),
                "status": "draft",
                "created_by": get_current_user().get("username", ""),
                "created_at": now_str(),
                "updated_at": now_str(),
            }
            sheets_db.add_record("kgb", record)
            _reload()
            log_activity("buat_kgb", f"Buat KGB: {pegawai['nama']} - {nomor_surat}")
            st.success(f"KGB berhasil dibuat! Nomor: {nomor_surat}")


def _monitor_kgb():
    st.markdown("#### 🔔 Monitoring Jatuh Tempo KGB")
    df = sheets_db.get_dataframe("kgb")
    if df.empty:
        st.info("Belum ada data KGB.")
        return

    if "jatuh_tempo" not in df.columns:
        st.warning("Kolom jatuh_tempo tidak ditemukan.")
        return

    df["days_left"] = df["jatuh_tempo"].apply(days_until_kgb)
    df["stat"] = df["jatuh_tempo"].apply(kgb_status)

    # Summary cards
    overdue = len(df[df["stat"] == "overdue"])
    urgent = len(df[df["stat"] == "urgent"])
    upcoming = len(df[df["stat"] == "upcoming"])

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Terlambat", overdue)
    c2.metric("🟡 Mendesak (≤30 hari)", urgent)
    c3.metric("🔵 Segera (≤90 hari)", upcoming)

    st.markdown("---")

    # Filter
    filter_stat = st.selectbox("Filter Status", ["Semua", "overdue", "urgent", "upcoming", "ok"], key="mon_kgb")

    display = df.copy()
    if filter_stat != "Semua":
        display = display[display["stat"] == filter_stat]

    display = display.sort_values("days_left")

    for _, row in display.iterrows():
        badge = kgb_status_badge(row["stat"])
        days = row["days_left"]
        days_text = f"terlambat {abs(days)} hari" if days < 0 else f"{days} hari lagi"
        border_color = "#c62828" if days < 0 else "#ef6c00" if days <= 30 else "#0277bd"

        st.markdown(f"""
        <div style="background:white; padding:12px 16px; border-radius:8px;
            margin-bottom:8px; border-left:4px solid {border_color};
            box-shadow:0 1px 3px rgba(0,0,0,0.06); display:flex; justify-content:space-between; align-items:center;">
            <div>
                <strong>{row.get('nama', '-')}</strong>
                &nbsp;·&nbsp; {row.get('nip', '-')}
                &nbsp;·&nbsp; Gol. {row.get('golongan', '-')}
                &nbsp;·&nbsp; Jatuh tempo: {format_date(row.get('jatuh_tempo', ''))}
            </div>
            <div>{badge} <span style="font-size:0.8rem; color:#546e7a;">({days_text})</span></div>
        </div>
        """, unsafe_allow_html=True)


def _do_generate_kgb(kgb_data: dict):
    pegawai = sheets_db.find_one_by_field("pegawai", "id", kgb_data.get("pegawai_id", ""))
    if not pegawai:
        st.error("Data pegawai tidak ditemukan.")
        return

    doc_data = {**kgb_data, **pegawai}
    try:
        doc_buffer = generate_kgb_doc(doc_data)
        log_activity("generate_kgb", f"Generate dokumen KGB: {kgb_data.get('nama', '-')}")
        st.download_button(
            label="📥 Download KGB (DOCX)",
            data=doc_buffer,
            file_name=f"KGB_{kgb_data.get('nama', 'doc')}_{datetime.now().strftime('%Y%m%d')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        st.success("Dokumen KGB berhasil di-generate!")
    except Exception as e:
        st.error(f"Gagal generate dokumen: {e}")


def _preview_kgb():
    kgb = st.session_state.get("preview_kgb")
    if not kgb:
        return

    pegawai = sheets_db.find_one_by_field("pegawai", "id", kgb.get("pegawai_id", ""))
    merged = {**(pegawai or {}), **kgb}

    st.markdown("#### 👁️ Preview KGB")
    st.markdown(f"""
    <div style="background:white; padding:2rem; border-radius:12px; box-shadow:0 2px 8px rgba(0,0,0,0.08);
        max-width:700px; margin:auto; font-family:'Source Sans 3',sans-serif; line-height:1.8;">

    <div style="text-align:center; margin-bottom:1.5rem;">
        <h3 style="margin:0; color:#1a237e;">KENAIKAN GAJI BERKALA</h3>
        <p style="color:#546e7a; font-size:0.9rem;">Nomor: {kgb.get('nomor_surat', '-')}</p>
    </div>

    <table style="width:100%; font-size:0.95rem;">
        <tr><td style="width:180px; font-weight:600;">Nama</td><td>: {merged.get('nama', '-')}</td></tr>
        <tr><td style="font-weight:600;">NIP</td><td>: {merged.get('nip', '-')}</td></tr>
        <tr><td style="font-weight:600;">Golongan</td><td>: {merged.get('golongan', '-')}</td></tr>
        <tr><td style="font-weight:600;">Jabatan</td><td>: {merged.get('jabatan', '-')}</td></tr>
        <tr><td style="font-weight:600;">Unit Kerja</td><td>: {merged.get('unit_kerja', '-')}</td></tr>
        <tr><td style="font-weight:600;">TMT Golongan</td><td>: {format_date(kgb.get('tmt_golongan', ''))}</td></tr>
        <tr><td style="font-weight:600;">Jatuh Tempo KGB</td><td>: {format_date(kgb.get('jatuh_tempo', ''))}</td></tr>
        <tr><td style="font-weight:600;">Gaji Lama</td><td>: {format_currency(kgb.get('gaji_lama', '0'))}</td></tr>
        <tr><td style="font-weight:600;">Gaji Baru</td><td>: {format_currency(kgb.get('gaji_baru', '0'))}</td></tr>
        <tr><td style="font-weight:600;">Status</td><td>: {kgb.get('status', '-')}</td></tr>
    </table>

    <div style="margin-top:2rem; padding-top:1rem; border-top:1px solid #e0e0e0; text-align:center;">
        <p style="color:#90a4ae; font-size:0.8rem;">Preview — Dokumen ini belum ditandatangani</p>
    </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("📄 Generate & Download", key="prev_kgb_gen"):
        _do_generate_kgb(kgb)

    if st.button("❌ Tutup Preview"):
        del st.session_state["preview_kgb"]
        st.rerun()
