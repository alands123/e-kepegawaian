"""
sheets_db.py — Google Sheets Database Layer
Provides all CRUD operations, caching, retry logic, and connection management.
"""

import gspread
import streamlit as st
import pandas as pd
from google.oauth2.service_account import Credentials
import time
import json
from datetime import datetime


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

@st.cache_resource(ttl=3600)
def get_gspread_client():
    """Return a cached gspread client authenticated via service account."""
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        # Support both nested (secrets.toml) and flat (HuggingFace) formats
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        else:
            creds_dict = {
                "type": st.secrets.get("GCP_SERVICE_ACCOUNT_TYPE", "service_account"),
                "project_id": st.secrets.get("GCP_SERVICE_ACCOUNT_PROJECT_ID", ""),
                "private_key_id": st.secrets.get("GCP_SERVICE_ACCOUNT_PRIVATE_KEY_ID", ""),
                "private_key": st.secrets.get("GCP_SERVICE_ACCOUNT_PRIVATE_KEY", "").replace("\\n", "\n"),
                "client_email": st.secrets.get("GCP_SERVICE_ACCOUNT_CLIENT_EMAIL", ""),
                "client_id": st.secrets.get("GCP_SERVICE_ACCOUNT_CLIENT_ID", ""),
                "auth_uri": st.secrets.get("GCP_SERVICE_ACCOUNT_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": st.secrets.get("GCP_SERVICE_ACCOUNT_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": st.secrets.get("GCP_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": st.secrets.get("GCP_SERVICE_ACCOUNT_CLIENT_X509_CERT_URL", ""),
            }

        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Gagal terhubung ke Google Sheets: {e}")
        st.stop()


def get_spreadsheet():
    """Return the main spreadsheet object."""
    client = get_gspread_client()
    # Support both nested and flat formats
    app_secrets = st.secrets.get("app", {})
    if isinstance(app_secrets, dict) and app_secrets:
        name = app_secrets.get("spreadsheet_name", "e-Kepegawaian Database")
    else:
        name = st.secrets.get("APP_SPREADSHEET_NAME", "e-Kepegawaian Database")
    try:
        return client.open(name)
    except gspread.SpreadsheetNotFound:
        st.error(
            f"Spreadsheet '{name}' tidak ditemukan. "
            "Pastikan sudah di-share ke service account."
        )
        st.stop()


# ---------------------------------------------------------------------------
# Sheet helpers
# ---------------------------------------------------------------------------

SHEET_HEADERS = {
    "users": [
        "id", "username", "password_hash", "fullname", "role", "email",
        "phone", "active", "last_login", "created_at",
    ],
    "pegawai": [
        "id", "nip", "nama", "tempat_lahir", "tanggal_lahir", "jenis_kelamin",
        "agama", "golongan", "pangkat", "jabatan", "unit_kerja", "pendidikan",
        "alamat", "telepon", "email", "tmt_golongan", "tmt_jabatan",
        "tmt_cpns", "tmt_pns", "status", "created_at", "updated_at",
    ],
    "kp4": [
        "id", "pegawai_id", "nip", "nama", "tanggal_pengajuan", "nomor_surat",
        "perihal", "keterangan", "status", "created_by", "created_at", "updated_at",
    ],
    "kgb": [
        "id", "pegawai_id", "nip", "nama", "golongan", "tmt_golongan",
        "jatuh_tempo", "gaji_lama", "gaji_baru", "tanggal_pengajuan",
        "nomor_surat", "keterangan", "status", "created_by",
        "created_at", "updated_at",
    ],
    "logs": [
        "id", "user", "action", "details", "timestamp",
    ],
    "notifications": [
        "id", "user_id", "title", "message", "type", "is_read", "created_at",
    ],
    "settings": [
        "key", "value", "description", "updated_at",
    ],
}


def _get_or_create_sheet(tab_name: str):
    """Get a worksheet by name; create it with headers if missing."""
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        headers = SHEET_HEADERS.get(tab_name, [])
        ws = ss.add_worksheet(title=tab_name, rows=1000, cols=len(headers) + 5)
        if headers:
            ws.update(range_name="A1", values=[headers])
        # Re-fetch to ensure clean state
        ws = ss.worksheet(tab_name)
    return ws


def init_all_sheets():
    """Ensure every required sheet tab exists with correct headers."""
    for tab, headers in SHEET_HEADERS.items():
        ws = _get_or_create_sheet(tab)
        existing = ws.row_values(1)
        if existing != headers:
            ws.update(range_name="A1", values=[headers])


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def get_all_records(tab_name: str) -> list[dict]:
    """Return all records from a sheet tab as a list of dicts."""
    ws = _get_or_create_sheet(tab_name)
    records = ws.get_all_records()
    return records


def get_dataframe(tab_name: str) -> pd.DataFrame:
    """Return records as a pandas DataFrame."""
    records = get_all_records(tab_name)
    if not records:
        headers = SHEET_HEADERS.get(tab_name, [])
        return pd.DataFrame(columns=headers)
    return pd.DataFrame(records)


def find_by_field(tab_name: str, field: str, value) -> list[dict]:
    """Find records where `field` == `value`."""
    records = get_all_records(tab_name)
    return [r for r in records if str(r.get(field, "")) == str(value)]


def find_one_by_field(tab_name: str, field: str, value):
    """Return the first matching record or None."""
    results = find_by_field(tab_name, field, value)
    return results[0] if results else None


def add_record(tab_name: str, record: dict, max_retries: int = 3):
    """Append a new record to the sheet. Returns the new row number."""
    ws = _get_or_create_sheet(tab_name)
    headers = SHEET_HEADERS.get(tab_name, ws.row_values(1))
    row = [record.get(h, "") for h in headers]
    for attempt in range(max_retries):
        try:
            ws.append_row(row, value_input_option="USER_ENTERED")
            # Invalidate cache
            get_all_records.clear()
            return ws.row_count
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)


def update_record(tab_name: str, record_id: str, updates: dict, max_retries: int = 3):
    """Update a record identified by 'id' column."""
    ws = _get_or_create_sheet(tab_name)
    headers = SHEET_HEADERS.get(tab_name, ws.row_values(1))
    records = ws.get_all_records()

    for idx, rec in enumerate(records):
        if str(rec.get("id", "")) == str(record_id):
            row_num = idx + 2  # 1-indexed + header row
            for attempt in range(max_retries):
                try:
                    for key, val in updates.items():
                        if key in headers:
                            col_idx = headers.index(key) + 1
                            ws.update_cell(row_num, col_idx, str(val))
                    get_all_records.clear()
                    return True
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(1)
    return False


def delete_record(tab_name: str, record_id: str):
    """Delete a record by its 'id'."""
    ws = _get_or_create_sheet(tab_name)
    records = ws.get_all_records()
    for idx, rec in enumerate(records):
        if str(rec.get("id", "")) == str(record_id):
            row_num = idx + 2
            ws.delete_rows(row_num)
            get_all_records.clear()
            return True
    return False


def get_setting(key: str, default: str = "") -> str:
    """Get an application setting."""
    rec = find_one_by_field("settings", "key", key)
    if rec:
        return rec.get("value", default)
    return default


def set_setting(key: str, value: str, description: str = ""):
    """Set an application setting (upsert). Works without 'id' column."""
    ws = _get_or_create_sheet("settings")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Find existing row by key column (settings sheet has no 'id' column)
    records = ws.get_all_records()
    for idx, rec in enumerate(records):
        if str(rec.get("key", "")) == str(key):
            row_num = idx + 2  # 1-indexed + header row
            headers = SHEET_HEADERS.get("settings", [])
            updates = {"value": value, "description": description, "updated_at": now}
            for k, val in updates.items():
                if k in headers:
                    col_idx = headers.index(k) + 1
                    ws.update_cell(row_num, col_idx, str(val))
            get_all_records.clear()
            return

    # Not found — insert new row
    add_record("settings", {
        "key": key, "value": value, "description": description, "updated_at": now,
    })
