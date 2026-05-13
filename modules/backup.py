"""
backup.py — Backup & Restore System
"""

import streamlit as st
import json
import io
from datetime import datetime
from modules import sheets_db
from modules.utils import now_str
from modules.auth import require_role
from modules.logs import log_activity


def render():
    require_role(["admin"])
    st.markdown("""
    <h1 style="color:#1a237e; font-family:'Plus Jakarta Sans',sans-serif;
        font-weight:800; font-size:1.8rem;">💾 Backup & Restore</h1>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["📤 Backup Data", "📥 Restore Data"])

    with tabs[0]:
        _backup_section()
    with tabs[1]:
        _restore_section()


def _backup_section():
    st.markdown("#### 📤 Backup Database")
    st.info("Backup akan meng-export semua sheet menjadi file JSON yang dapat di-download.")

    sheets_to_backup = ["pegawai", "kp4", "kgb", "users", "logs", "notifications", "settings"]
    selected = st.multiselect("Pilih sheet untuk di-backup", sheets_to_backup, default=sheets_to_backup)

    if st.button("🚀 Generate Backup", use_container_width=True):
        backup_data = {}
        for sheet in selected:
            try:
                records = sheets_db.get_all_records(sheet)
                backup_data[sheet] = records
            except Exception as e:
                st.warning(f"Gagal backup sheet '{sheet}': {e}")

        backup_data["_meta"] = {
            "created_at": now_str(),
            "version": "1.0",
            "sheets": selected,
        }

        json_str = json.dumps(backup_data, indent=2, ensure_ascii=False, default=str)
        filename = f"backup_ekepeg_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        st.download_button(
            "📥 Download Backup",
            data=json_str,
            file_name=filename,
            mime="application/json",
            use_container_width=True,
        )
        log_activity("backup", f"Backup {len(selected)} sheet")
        st.success(f"Backup berhasil! File: {filename}")


def _restore_section():
    st.markdown("#### 📥 Restore Database")
    st.warning("PERINGATAN: Restore akan menimpa data yang ada. Pastikan Anda sudah memiliki backup terbaru.")

    file = st.file_uploader("Upload file backup (.json)", type=["json"])

    if file:
        try:
            backup_data = json.load(file)
            meta = backup_data.get("_meta", {})
            sheets = [k for k in backup_data.keys() if not k.startswith("_")]

            st.markdown(f"""
            - **Waktu backup**: {meta.get('created_at', '-')}
            - **Sheets**: {', '.join(sheets)}
            """)

            for sheet in sheets:
                records = backup_data[sheet]
                st.write(f"  - {sheet}: {len(records)} records")

            if st.button("⚠️ Konfirmasi Restore", type="primary", use_container_width=True):
                for sheet in sheets:
                    records = backup_data[sheet]
                    # Clear existing data (except header)
                    ws = sheets_db._get_or_create_sheet(sheet)
                    if ws.row_count > 1:
                        ws.delete_rows(2, ws.row_count)
                    # Write backup data
                    if records:
                        headers = sheets_db.SHEET_HEADERS.get(sheet, list(records[0].keys()))
                        rows = [[r.get(h, "") for h in headers] for r in records]
                        ws.append_rows(rows, value_input_option="USER_ENTERED")

                sheets_db.get_all_records.clear()
                log_activity("restore", f"Restore {len(sheets)} sheet")
                st.success("Restore berhasil!")
                st.balloons()
                st.rerun()

        except json.JSONDecodeError:
            st.error("File tidak valid. Upload file .json backup.")
        except Exception as e:
            st.error(f"Gagal restore: {e}")
