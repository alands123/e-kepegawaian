"""
export_data.py — Export reports to Excel, CSV, PDF.
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
from modules import sheets_db


def render():
    st.markdown("""
    <h1 style="color:#1a237e; font-family:'Plus Jakarta Sans',sans-serif;
        font-weight:800; font-size:1.8rem;">📥 Export Laporan</h1>
    """, unsafe_allow_html=True)

    export_type = st.selectbox("Pilih Data", [
        "Data Pegawai", "Data KP4", "Data KGB", "Log Aktivitas"
    ])

    sheet_map = {
        "Data Pegawai": "pegawai",
        "Data KP4": "kp4",
        "Data KGB": "kgb",
        "Log Aktivitas": "logs",
    }
    sheet_name = sheet_map[export_type]

    df = sheets_db.get_dataframe(sheet_name)

    if df.empty:
        st.info(f"Tidak ada data {export_type}.")
        return

    # Filter
    st.markdown("#### 🔍 Filter Data")

    if sheet_name == "pegawai":
        col1, col2 = st.columns(2)
        with col1:
            if "status" in df.columns:
                f_status = st.selectbox("Status", ["Semua"] + sorted(df["status"].dropna().unique().tolist()))
                if f_status != "Semua":
                    df = df[df["status"] == f_status]
        with col2:
            if "golongan" in df.columns:
                f_gol = st.selectbox("Golongan", ["Semua"] + sorted(df["golongan"].dropna().unique().tolist()))
                if f_gol != "Semua":
                    df = df[df["golongan"] == f_gol]

    st.write(f"Total data: {len(df)} baris")
    st.dataframe(df.head(20), use_container_width=True)

    # Export buttons
    st.markdown("---")
    st.markdown("#### 📥 Download")

    col1, col2, col3 = st.columns(3)

    filename_base = f"{export_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    with col1:
        # Excel export
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Data")
        excel_buffer.seek(0)
        st.download_button(
            "📊 Download Excel",
            data=excel_buffer,
            file_name=f"{filename_base}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col2:
        # CSV export
        csv_data = df.to_csv(index=False)
        st.download_button(
            "📄 Download CSV",
            data=csv_data,
            file_name=f"{filename_base}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col3:
        # PDF-like: Print-ready HTML
        html = _generate_html_report(df, export_type)
        st.download_button(
            "📑 Download HTML",
            data=html,
            file_name=f"{filename_base}.html",
            mime="text/html",
            use_container_width=True,
        )


def _generate_html_report(df: pd.DataFrame, title: str) -> str:
    """Generate a styled HTML report."""
    now = datetime.now().strftime("%d %B %Y %H:%M")
    table_html = df.to_html(index=False, classes="report-table", border=0, na_rep="-")

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>{title} - e-Kepegawaian</title>
<style>
    body {{ font-family: 'Source Sans 3', 'Segoe UI', sans-serif; margin: 40px; color: #1a1a2e; }}
    h1 {{ color: #1a237e; font-size: 1.6rem; margin-bottom: 4px; }}
    .meta {{ color: #546e7a; font-size: 0.85rem; margin-bottom: 24px; }}
    .report-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    .report-table th {{ background: #1a237e; color: white; padding: 10px 12px; text-align: left; font-weight: 600; }}
    .report-table td {{ padding: 8px 12px; border-bottom: 1px solid #e0e0e0; }}
    .report-table tr:nth-child(even) {{ background: #f5f7fa; }}
    .report-table tr:hover {{ background: #e8eaf6; }}
    .footer {{ margin-top: 32px; color: #90a4ae; font-size: 0.8rem; text-align: center; }}
    @media print {{ body {{ margin: 20px; }} }}
</style>
</head><body>
<h1>{title}</h1>
<p class="meta">e-Kepegawaian · {now} · Total: {len(df)} data</p>
{table_html}
<p class="footer">Dicetak dari Sistem e-Kepegawaian</p>
</body></html>"""
