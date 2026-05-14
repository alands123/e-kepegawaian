---
title: e-Kepegawaian
emoji: 🏛️
colorFrom: indigo
colorTo: yellow
sdk: streamlit
sdk_version: 1.45.0
app_file: app.py
pinned: false
license: mit
---

# 🏛️ e-Kepegawaian

**Sistem Arsip & Manajemen Data Kepegawaian** berbasis web untuk instansi
pemerintah, sekolah, dan dinas.

## Fitur Utama

| Modul | Deskripsi |
|---|---|
| 📊 Dashboard | Statistik pegawai, grafik, reminder KGB, aktivitas terbaru |
| 👤 Data Pegawai | CRUD, pencarian, import/export Excel |
| 📄 KP4 | Pengajuan, generate dokumen otomatis, preview, download |
| 📊 KGB | Kenaikan gaji berkala, monitoring jatuh tempo, generate surat |
| 📥 Export | Laporan Excel, CSV, HTML |
| 🔔 Notifikasi | Reminder otomatis KGB, status dokumen |
| 📋 Audit Log | Pelacakan semua aktivitas pengguna |
| 💾 Backup | Backup & restore database JSON |
| ⚙️ Pengaturan | Manajemen user, instansi, template dokumen |

## Stack Teknologi

- **Backend:** Python 3.11+ / Streamlit
- **Database:** Google Sheets API (gspread)
- **Auth:** Custom bcrypt + session management
- **Document:** python-docx / docxtpl
- **Charts:** Plotly

## Instalasi Lokal

```bash
# 1. Clone repository
git clone https://github.com/alands123/e-kepegawaian.git
cd e-kepegawaian

# 2. Buat virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml dengan credentials Anda

# 5. Jalankan aplikasi
streamlit run app.py
```

## Deploy ke HuggingFace Spaces (GRATIS)

### Langkah 1 — Buat Space

1. Buka [huggingface.co/new-space](https://huggingface.co/new-space)
2. Isi:
   - **Space name:** `e-kepegawaian`
   - **License:** MIT
   - **SDK:** Streamlit
   - **Visibility:** Private ⚠️ (karena ada data pegawai & credentials)
3. Klik **Create Space**

### Langkah 2 — Push kode

```bash
# Tambah remote HuggingFace
git remote add hf https://huggingface.co/spaces/NAMA_KAMU/e-kepegawaian

# Push ke HuggingFace
git push hf main
```

### Langkah 3 — Setup Secrets

Buka **Settings** di Space kamu → **Repository secrets**, lalu tambahkan:

| Nama Secret | Isi |
|---|---|
| `GCP_SERVICE_ACCOUNT_TYPE` | `service_account` |
| `GCP_SERVICE_ACCOUNT_PROJECT_ID` | project ID dari GCP |
| `GCP_SERVICE_ACCOUNT_PRIVATE_KEY_ID` | dari file JSON |
| `GCP_SERVICE_ACCOUNT_PRIVATE_KEY` | isi private key (termasuk BEGIN/END) |
| `GCP_SERVICE_ACCOUNT_CLIENT_EMAIL` | email service account |
| `GCP_SERVICE_ACCOUNT_CLIENT_ID` | client ID |
| `GCP_SERVICE_ACCOUNT_AUTH_URI` | `https://accounts.google.com/o/oauth2/auth` |
| `GCP_SERVICE_ACCOUNT_TOKEN_URI` | `https://oauth2.googleapis.com/token` |
| `GCP_SERVICE_ACCOUNT_AUTH_PROVIDER_X509_CERT_URL` | `https://www.googleapis.com/oauth2/v1/certs` |
| `GCP_SERVICE_ACCOUNT_CLIENT_X509_CERT_URL` | dari file JSON |
| `APP_SPREADSHEET_NAME` | `e-Kepegawaian Database` |
| `APP_DEFAULT_ADMIN_PASSWORD` | `Admin@2026` |
| `AUTH_COOKIE_KEY` | random string 32+ karakter |

## Default Login

| Username | Password | Role |
|---|---|---|
| admin | Admin@2026 | admin |

⚠️ Segera ganti password setelah login pertama kali!

## Struktur Folder

```
e-kepegawaian/
├── app.py              # Entry point
├── requirements.txt    # Dependencies
├── .streamlit/         # Config & secrets
├── assets/css/         # Custom CSS
└── modules/            # Modul aplikasi
    ├── sheets_db.py    # Database layer
    ├── auth.py         # Authentication
    ├── dashboard.py    # Dashboard
    ├── pegawai.py      # Data pegawai
    ├── kp4.py          # Modul KP4
    ├── kgb.py          # Modul KGB
    ├── generate_doc.py # Document generator
    ├── export_data.py  # Export laporan
    ├── logs.py         # Audit log
    ├── notifications.py # Notifikasi
    ├── backup.py       # Backup & restore
    ├── settings.py     # Pengaturan
    └── utils.py        # Utilities
```

## Lisensi

MIT License — Bebas digunakan dan dikembangkan.
