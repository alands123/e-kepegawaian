markdown
markdown
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
- **Deploy:** Streamlit Community Cloud (GRATIS)

## Instalasi Lokal

```bash
# 1. Clone repository
git clone https://github.com/username/e-kepegawaian.git
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

Setup Google Sheets API

1.Buka 
Google Cloud Console
2.Buat project baru
3.Aktifkan Google Sheets API dan Google Drive API
4.Buat Service Account → Download JSON credential
5.Buat Google Spreadsheet bernama "e-Kepegawaian Database"
6.Share spreadsheet ke email service account (Editor access)
7.Copy isi JSON ke .streamlit/secrets.toml

Deploy ke Streamlit Cloud

1.Push kode ke GitHub
2.Login ke 
Streamlit Cloud
3.Klik New app → Pilih repository
4.Set main file: app.py
5.Klik Advanced settings → Paste isi secrets.toml
6.Klik Deploy

Default Login

Username	Password	Role
admin	Admin@2026	admin

⚠️ Segera ganti password setelah login pertama kali!


Struktur Folder

text
text
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

Lisensi

MIT License — Bebas digunakan dan dikembangkan.

text
text

---

## Panduan Deployment Lengkap

### Langkah 1 — Google Cloud Console

1.Buka console.cloud.google.com
2.Buat Project baru → "e-Kepegawaian"
3.Menu: APIs & Services → Enable API
Google Sheets API → Enable
Google Drive API → Enable
4.Menu: IAM & Admin → Service Accounts → Create
Name: ekepeg-service
Role: Editor
Create Key → JSON → Download
5.Salin isi file JSON ke secrets.toml
text
text

### Langkah 2 — Google Spreadsheet

1.Buka sheets.google.com
2.Buat Spreadsheet baru → Nama: "e-Kepegawaian Database"
3.Klik Share → Tambahkan email service account
(format: 
xxxxx@project-id.iam.gserviceaccount.com
)
4.Beri akses "Editor"
5.Sheet akan otomatis terisi tab saat app pertama dijalankan
text
text

### Langkah 3 — GitHub

```bash
mkdir e-kepegawaian && cd e-kepegawaian
git init

# (copy semua file ke struktur folder yang sesuai)

git add .
git commit -m "Initial commit: e-Kepegawaian v1.0"
git branch -M main
git remote add origin https://github.com/USERNAME/e-kepegawaian.git
git push -u origin main

Langkah 4 — Streamlit Cloud

text
text
1. Buka share.streamlit.io
2. Login dengan GitHub
3. Klik "New app"
4. Repository: USERNAME/e-kepegawaian
5. Branch: main
6. Main file: app.py
7. Klik "Advanced settings"
8. Paste isi secrets.toml ke kolom Secrets
9. Klik "Deploy!"

Langkah 5 — Verifikasi

text
text
1. Tunggu deployment selesai (~2-5 menit)
2. Aplikasi terbuka di URL: https://xxx.streamlit.app
3. Login dengan: admin / Admin@2026
4. Test semua menu
5. Ganti password admin di Pengaturan


Semua kode di atas saling terintegrasi dan siap deploy. Setiap modul memiliki error handling, input validation, dan audit logging. UI menggunakan tema pemerintah profesional dengan warna navy, kartu modern, dan responsif untuk mobile. Aplikasi ini gratis di-deploy di Streamlit Community Cloud tanpa biaya server.
