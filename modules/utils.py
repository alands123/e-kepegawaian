"""
utils.py — Shared utilities for e-Kepegawaian.
"""

import uuid
import re
import hashlib
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import streamlit as st


# ---------------------------------------------------------------------------
# ID & Timestamps
# ---------------------------------------------------------------------------

def generate_id() -> str:
    return str(uuid.uuid4())[:12]


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_date(date_str: str, fmt: str = "%d %B %Y") -> str:
    if not date_str:
        return "-"
    try:
        dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
        months_id = {
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
            5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
            9: "September", 10: "Oktober", 11: "November", 12: "Desember",
        }
        return f"{dt.day} {months_id[dt.month]} {dt.year}"
    except (ValueError, TypeError):
        return str(date_str)


def format_date_short(date_str: str) -> str:
    return format_date(date_str, "%d-%m-%Y")


def format_currency(amount) -> str:
    try:
        val = int(float(str(amount).replace(",", "").replace(".", "")))
        return f"Rp {val:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "Rp 0"


def format_nip(nip: str) -> str:
    """Format NIP: 123456789012345678 → 1234567 890123 4 5678"""
    nip = str(nip).strip()
    if len(nip) == 18:
        return f"{nip[:8]} {nip[8:14]} {nip[14]} {nip[15:]}"
    return nip


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_nip(nip: str) -> bool:
    nip = str(nip).strip()
    return bool(re.match(r'^\d{18}$', nip))


def validate_email(email: str) -> bool:
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))


def sanitize_input(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'[<>"\';]', '', text)
    return text.strip()


# ---------------------------------------------------------------------------
# Auto Numbering
# ---------------------------------------------------------------------------

def generate_nomor_surat(jenis: str, tahun: int, nomor: int) -> str:
    """Generate nomor surat: 800/KGB/2026/001"""
    kode = {"kp4": "KP4", "kgb": "KGB", "sk": "SK"}
    prefix = kode.get(jenis.lower(), jenis.upper())
    return f"800/{prefix}/{tahun}/{nomor:03d}"


def generate_nomor_arsip(jenis: str, nomor: int) -> str:
    return f"ARS/{jenis.upper()}/{datetime.now().year}/{nomor:05d}"


# ---------------------------------------------------------------------------
# KGB Calculations
# ---------------------------------------------------------------------------

GOLONGAN_LIST = [
    "I/a", "I/b", "I/c", "I/d",
    "II/a", "II/b", "II/c", "II/d",
    "III/a", "III/b", "III/c", "III/d",
    "IV/a", "IV/b", "IV/c", "IV/d", "IV/e",
]

PANGKAT_LIST = [
    "Juru Muda", "Juru Muda Tingkat I", "Juru", "Juru Tingkat I",
    "Pengatur Muda", "Pengatur Muda Tingkat I", "Pengatur", "Pengatur Tingkat I",
    "Penata Muda", "Penata Muda Tingkat I", "Penata", "Penata Tingkat I",
    "Pembina", "Pembina Tingkat I", "Pembina Utama Muda",
    "Pembina Utama Madya", "Pembina Utama",
]

# Mapping golongan → masa kerja KGB dalam bulan
KGB_PERIOD = {g: 48 for g in GOLONGAN_LIST}  # Default 4 tahun


def calculate_jatuh_tempo(tmt_golongan: str, period_months: int = 48) -> str:
    """Calculate KGB due date from TMT golongan."""
    try:
        tmt = datetime.strptime(str(tmt_golongan)[:10], "%Y-%m-%d")
        due = tmt + relativedelta(months=period_months)
        return due.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return ""


def days_until_kgb(jatuh_tempo: str) -> int:
    """Return days until KGB due date (negative = overdue)."""
    try:
        due = datetime.strptime(str(jatuh_tempo)[:10], "%Y-%m-%d")
        return (due - datetime.now()).days
    except (ValueError, TypeError):
        return 999


def kgb_status(jatuh_tempo: str) -> str:
    """Return KGB status: overdue, urgent, upcoming, ok."""
    days = days_until_kgb(jatuh_tempo)
    if days < 0:
        return "overdue"
    elif days <= 30:
        return "urgent"
    elif days <= 90:
        return "upcoming"
    return "ok"


def kgb_status_badge(status: str) -> str:
    """Return an HTML badge for KGB status."""
    badges = {
        "overdue": '<span class="badge badge-danger">TERLAMBAT</span>',
        "urgent": '<span class="badge badge-warning">MENDESAK</span>',
        "upcoming": '<span class="badge badge-info">SEGERA</span>',
        "ok": '<span class="badge badge-success">AMAN</span>',
    }
    return badges.get(status, '<span class="badge badge-primary">-</span>')


# ---------------------------------------------------------------------------
# Password helpers (for initial setup only; auth.py handles runtime)
# ---------------------------------------------------------------------------

def hash_password_simple(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password_simple(password: str, hashed: str) -> bool:
    import bcrypt
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Status label helpers
# ---------------------------------------------------------------------------

STATUS_BADGE_MAP = {
    "draft": "badge-primary",
    "diajukan": "badge-info",
    "diproses": "badge-warning",
    "disetujui": "badge-success",
    "ditolak": "badge-danger",
    "selesai": "badge-success",
    "aktif": "badge-success",
    "nonaktif": "badge-danger",
    "pns": "badge-success",
    "cpns": "badge-info",
    "honorer": "badge-warning",
}


def status_badge(status: str) -> str:
    cls = STATUS_BADGE_MAP.get(str(status).lower(), "badge-primary")
    return f'<span class="badge {cls}">{status.upper() if status else "-"}</span>'
