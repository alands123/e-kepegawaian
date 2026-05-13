"""
pegawai.py — Master Data Pegawai (CRUD, Search, Detail, Import/Export)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from modules import sheets_db
from modules.utils import (
    generate_id, now_str, today_str, sanitize_input,
    format_nip, format_date, format_currency,
    GOLONGAN_LIST, PANGKAT_LIST, status_badge, validate_nip,
)
from modules.auth import get_current_user, require_auth, has_role
from modules.logs import log_activity


def _reload():
    sheets_db.get_all_records.clear()


def render():
    require_auth()
    st.markdown("""
    <h1 style="color:#1a237e; font-family:'Plus Jakarta Sans',sans-serif;
        font-weight:800; font-size:1.8rem;">👤 Master Data Pegawai</h1>
    """, unsafe_allow_html=True)

    # Sub-navigation
    tabs = ["📋 Daftar Pegawai", "➕ Tambah Pegawai", "📤 Import Data"]
    if st.session_state.get("edit_pegawai_id"):
        tabs.append("✏️ Edit Pegawai")
    if st.session_state.get("detail_pegawai_id"):
        tabs.append("🔍 Detail Pegawai")

    selected = st.tabs(tabs)

    with selected[0]:
        _list_pegawai()
    with selected[1]:
        _form_tambah()
    with selected[2]:
        _import_data()

    tab_idx = 3
    if st.session_state.get("edit_pegawai_id"):
        with selected[tab_idx]:
            _form_edit(st.session_state["edit_pegawai_id"])
        tab_idx += 1
    if st.session_state.get("detail_pegawai_id"):
        with selected[tab_idx]:
            _detail_pegawai(st.session_state["detail_pegawai_id"])


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

def _list_pegawai():
    df = sheets_db.get_dataframe("pegawai")
    if df.empty:
        st.info("Belum ada data pegawai. Silakan tambah data atau import.")
        return

    # Search & Filter
    col_search, col_filter, col_filter2 = st.columns([3, 1, 1])
    with col_search:
        search = st.text_input("🔍 Cari pegawai", placeholder="Nama / NIP / Jabatan...")
    with col_filter:
        if "status" in df.columns:
            status_opts = ["Semua"] + sorted(df["status"].dropna().unique().tolist())
            f_status = st.selectbox("Status", status_opts)
        else:
            f_status = "Semua"
    with col_filter2:
        if "golongan" in df.columns:
            gol_opts = ["Semua"] + sorted(df["golongan"].dropna().unique().tolist())
            f_gol = st.selectbox("Golongan", gol_opts)
        else:
            f_gol = "Semua"

    # Apply filters
    filtered = df.copy()
    if search:
        mask = (
            filtered.astype(str).apply(
                lambda row: row.str.contains(search, case=False, na=False).any(), axis=1
            )
        )
        filtered = filtered[mask]
    if f_status != "Semua" and "status" in filtered.columns:
        filtered = filtered[filtered["status"] == f_status]
    if f_gol != "Semua" and "golongan" in filtered.columns:
        filtered = filtered[filtered["golongan"] == f_gol]

    st.markdown(f"<p style='color:#546e7a;'>Menampilkan {len(filtered)} dari {len(df)} pegawai</p>",
                unsafe_allow_html=True)

    # Display table
    display_cols = [c for c in ["nip", "nama", "golongan", "jabatan", "unit_kerja", "status"]
                    if c in filtered.columns]
    if display_cols:
        st.dataframe(
            filtered[display_cols].reset_index(drop=True),
            use_container_width=True,
            height=400,
            column_config={
                "nip": st.column_config.TextColumn("NIP", width="medium"),
                "nama": st.column_config.TextColumn("Nama", width="medium"),
                "golongan": st.column_config.TextColumn("Gol.", width="small"),
                "jabatan": st.column_config.TextColumn("Jabatan", width="medium"),
                "unit_kerja": st.column_config.TextColumn("Unit Kerja", width="medium"),
                "status": st.column_config.TextColumn("Status", width="small"),
            },
        )

    # Action buttons
    st.markdown("---")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        selected_nip = st.text_input("NIP Pegawai untuk Detail/Edit", key="nip_action")
    with col_b:
        if st.button("🔍 Lihat Detail", use_container_width=True):
            if selected_nip:
                found = sheets_db.find_one_by_field("pegawai", "nip", selected_nip.strip())
                if found:
                    st.session_state["detail_pegawai_id"] = found["id"]
                    st.rerun()
                else:
                    st.error("Pegawai tidak ditemukan.")
    with col_c:
        if st.button("✏️ Edit Data", use_container_width=True):
            if selected_nip:
                found = sheets_db.find_one_by_field("pegawai", "nip", selected_nip.strip())
                if found:
                    st.session_state["edit_pegawai_id"] = found["id"]
                    st.rerun()
                else:
                    st.error("Pegawai tidak ditemukan.")


# ---------------------------------------------------------------------------
# Form Tambah
# ---------------------------------------------------------------------------

def _form_tambah():
    with st.form("form_tambah_pegawai", clear_on_submit=True):
        st.markdown("#### 📝 Form Tambah Pegawai")
        col1, col2 = st.columns(2)

        with col1:
            nip = st.text_input("NIP *", max_chars=18, placeholder="18 digit NIP")
            nama = st.text_input("Nama Lengkap *", placeholder="Nama sesuai SK")
            tempat_lahir = st.text_input("Tempat Lahir")
            tanggal_lahir = st.date_input("Tanggal Lahir", value=None, min_value=datetime(1960, 1, 1))
            jk = st.selectbox("Jenis Kelamin", ["", "Laki-laki", "Perempuan"])
            agama = st.selectbox("Agama", ["", "Islam", "Kristen", "Katolik", "Hindu", "Buddha", "Konghucu"])

        with col2:
            golongan = st.selectbox("Golongan", [""] + GOLONGAN_LIST)
            pangkat = st.selectbox("Pangkat", [""] + PANGKAT_LIST)
            jabatan = st.text_input("Jabatan")
            unit_kerja = st.text_input("Unit Kerja")
            pendidikan = st.selectbox("Pendidikan Terakhir",
                                      ["", "SMA", "D3", "S1", "S2", "S3"])
            status = st.selectbox("Status Kepegawaian", ["", "PNS", "CPNS", "Honorer", "PPPK"])

        col3, col4 = st.columns(2)
        with col3:
            tmt_golongan = st.date_input("TMT Golongan", value=None)
            tmt_cpns = st.date_input("TMT CPNS", value=None)
        with col4:
            tmt_jabatan = st.date_input("TMT Jabatan", value=None)
            tmt_pns = st.date_input("TMT PNS", value=None)

        alamat = st.text_area("Alamat")
        telepon = st.text_input("Telepon")
        email = st.text_input("Email")

        submitted = st.form_submit_button("💾 Simpan Data Pegawai", use_container_width=True)

        if submitted:
            if not nip or not nama:
                st.error("NIP dan Nama wajib diisi!")
                return
            if not validate_nip(nip):
                st.error("NIP harus 18 digit angka!")
                return
            existing = sheets_db.find_one_by_field("pegawai", "nip", nip.strip())
            if existing:
                st.error(f"NIP {nip} sudah terdaftar atas nama {existing.get('nama', '-')}")
                return

            record = {
                "id": generate_id(),
                "nip": nip.strip(),
                "nama": sanitize_input(nama),
                "tempat_lahir": sanitize_input(tempat_lahir),
                "tanggal_lahir": tanggal_lahir.strftime("%Y-%m-%d") if tanggal_lahir else "",
                "jenis_kelamin": jk,
                "agama": agama,
                "golongan": golongan,
                "pangkat": pangkat,
                "jabatan": sanitize_input(jabatan),
                "unit_kerja": sanitize_input(unit_kerja),
                "pendidikan": pendidikan,
                "alamat": sanitize_input(alamat),
                "telepon": sanitize_input(telepon),
                "email": sanitize_input(email),
                "tmt_golongan": tmt_golongan.strftime("%Y-%m-%d") if tmt_golongan else "",
                "tmt_jabatan": tmt_jabatan.strftime("%Y-%m-%d") if tmt_jabatan else "",
                "tmt_cpns": tmt_cpns.strftime("%Y-%m-%d") if tmt_cpns else "",
                "tmt_pns": tmt_pns.strftime("%Y-%m-%d") if tmt_pns else "",
                "status": status,
                "created_at": now_str(),
                "updated_at": now_str(),
            }
            sheets_db.add_record("pegawai", record)
            _reload()
            log_activity("tambah_pegawai", f"Tambah pegawai: {nama} ({nip})")
            st.success(f"Pegawai {nama} berhasil ditambahkan!")
            st.balloons()


# ---------------------------------------------------------------------------
# Form Edit
# ---------------------------------------------------------------------------

def _form_edit(pegawai_id: str):
    data = sheets_db.find_one_by_field("pegawai", "id", pegawai_id)
    if not data:
        st.error("Data pegawai tidak ditemukan.")
        return

    st.markdown(f"#### ✏️ Edit Data — {data.get('nama', '-')}")

    with st.form("form_edit_pegawai"):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Lengkap", value=data.get("nama", ""))
            jabatan = st.text_input("Jabatan", value=data.get("jabatan", ""))
            unit_kerja = st.text_input("Unit Kerja", value=data.get("unit_kerja", ""))
            golongan = st.selectbox("Golongan", GOLONGAN_LIST,
                                    index=GOLONGAN_LIST.index(data.get("golongan", "")) if data.get("golongan", "") in GOLONGAN_LIST else 0)
        with col2:
            status = st.selectbox("Status", ["PNS", "CPNS", "Honorer", "PPPK"],
                                  index=["PNS", "CPNS", "Honorer", "PPPK"].index(data.get("status", "PNS")) if data.get("status", "PNS") in ["PNS", "CPNS", "Honorer", "PPPK"] else 0)
            pangkat = st.text_input("Pangkat", value=data.get("pangkat", ""))
            telepon = st.text_input("Telepon", value=data.get("telepon", ""))
            email = st.text_input("Email", value=data.get("email", ""))

        alamat = st.text_area("Alamat", value=data.get("alamat", ""))

        if st.form_submit_button("💾 Simpan Perubahan", use_container_width=True):
            updates = {
                "nama": sanitize_input(nama),
                "jabatan": sanitize_input(jabatan),
                "unit_kerja": sanitize_input(unit_kerja),
                "golongan": golongan,
                "pangkat": pangkat,
                "status": status,
                "telepon": sanitize_input(telepon),
                "email": sanitize_input(email),
                "alamat": sanitize_input(alamat),
                "updated_at": now_str(),
            }
            sheets_db.update_record("pegawai", pegawai_id, updates)
            _reload()
            log_activity("edit_pegawai", f"Edit pegawai: {data.get('nama', '-')}")
            st.success("Data berhasil diperbarui!")
            del st.session_state["edit_pegawai_id"]
            st.rerun()

    if st.button("❌ Batal Edit"):
        del st.session_state["edit_pegawai_id"]
        st.rerun()


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------

def _detail_pegawai(pegawai_id: str):
    data = sheets_db.find_one_by_field("pegawai", "id", pegawai_id)
    if not data:
        st.error("Data tidak ditemukan.")
        return

    st.markdown(f"#### 🔍 Detail Pegawai — {data.get('nama', '-')}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        | Field | Nilai |
        |---|---|
        | **NIP** | {format_nip(data.get('nip', ''))} |
        | **Nama** | {data.get('nama', '-')} |
        | **Tempat/Tgl Lahir** | {data.get('tempat_lahir', '-')}, {format_date(data.get('tanggal_lahir', ''))} |
        | **Jenis Kelamin** | {data.get('jenis_kelamin', '-')} |
        | **Agama** | {data.get('agama', '-')} |
        | **Pendidikan** | {data.get('pendidikan', '-')} |
        | **Status** | {data.get('status', '-')} |
        """)

    with col2:
        st.markdown(f"""
        | Field | Nilai |
        |---|---|
        | **Golongan** | {data.get('golongan', '-')} |
        | **Pangkat** | {data.get('pangkat', '-')} |
        | **Jabatan** | {data.get('jabatan', '-')} |
        | **Unit Kerja** | {data.get('unit_kerja', '-')} |
        | **TMT Golongan** | {format_date(data.get('tmt_golongan', ''))} |
        | **TMT Jabatan** | {format_date(data.get('tmt_jabatan', ''))} |
        | **Telepon** | {data.get('telepon', '-')} |
        """)

    # History KGB & KP4
    st.markdown("---")
    df_kgb = sheets_db.get_dataframe("kgb")
    if not df_kgb.empty and "pegawai_id" in df_kgb.columns:
        riwayat_kgb = df_kgb[df_kgb["pegawai_id"] == pegawai_id]
        if not riwayat_kgb.empty:
            st.markdown("##### 📊 Riwayat KGB")
            st.dataframe(riwayat_kgb[["tanggal_pengajuan", "nomor_surat", "gaji_lama", "gaji_baru", "status"]],
                         use_container_width=True)

    if st.button("❌ Tutup Detail"):
        del st.session_state["detail_pegawai_id"]
        st.rerun()


# ---------------------------------------------------------------------------
# Import Data
# ---------------------------------------------------------------------------

def _import_data():
    st.markdown("#### 📤 Import Data Pegawai dari Excel/CSV")
    st.info("Format kolom: nip, nama, tempat_lahir, tanggal_lahir, jenis_kelamin, golongan, pangkat, jabatan, unit_kerja, status")

    file = st.file_uploader("Pilih file", type=["xlsx", "csv"])
    if file:
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            st.write(f"Preview: {len(df)} baris")
            st.dataframe(df.head(10), use_container_width=True)

            if st.button("🚀 Import Semua Data"):
                imported = 0
                skipped = 0
                for _, row in df.iterrows():
                    nip = str(row.get("nip", "")).strip()
                    if sheets_db.find_one_by_field("pegawai", "nip", nip):
                        skipped += 1
                        continue
                    record = {
                        "id": generate_id(),
                        "nip": nip,
                        "nama": str(row.get("nama", "")),
                        "tempat_lahir": str(row.get("tempat_lahir", "")),
                        "tanggal_lahir": str(row.get("tanggal_lahir", "")),
                        "jenis_kelamin": str(row.get("jenis_kelamin", "")),
                        "agama": str(row.get("agama", "")),
                        "golongan": str(row.get("golongan", "")),
                        "pangkat": str(row.get("pangkat", "")),
                        "jabatan": str(row.get("jabatan", "")),
                        "unit_kerja": str(row.get("unit_kerja", "")),
                        "pendidikan": str(row.get("pendidikan", "")),
                        "alamat": str(row.get("alamat", "")),
                        "telepon": str(row.get("telepon", "")),
                        "email": str(row.get("email", "")),
                        "tmt_golongan": str(row.get("tmt_golongan", "")),
                        "tmt_jabatan": str(row.get("tmt_jabatan", "")),
                        "tmt_cpns": str(row.get("tmt_cpns", "")),
                        "tmt_pns": str(row.get("tmt_pns", "")),
                        "status": str(row.get("status", "")),
                        "created_at": now_str(),
                        "updated_at": now_str(),
                    }
                    sheets_db.add_record("pegawai", record)
                    imported += 1
                _reload()
                log_activity("import_pegawai", f"Import {imported} pegawai, {skipped} dilewati")
                st.success(f"Berhasil import {imported} data. {skipped} data duplikat dilewati.")
        except Exception as e:
            st.error(f"Gagal import: {e}")
