import streamlit as st

# Konfigurasi halaman
st.set_page_config(
    page_title="Executive Maintenance & OEE System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling tema gelap profesional
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0B0F19 0%, #111827 50%, #0F172A 100%);
        color: #F3F4F6;
    }
    .card {
        background-color: #1E293B;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Judul Utama & Sambutan
st.title("⚡ Executive Maintenance & OEE System")
st.caption("Sistem Monitoring Terpadu Pabrik")
st.markdown("---")

st.markdown("""
<div class="card">
    <h3>Selamat Datang di Portal Maintenance & OEE</h3>
    <p>Silakan gunakan menu navigasi di <b>Sidebar sebelah kiri</b> untuk mengakses masing-masing halaman dengan link uniknya:</p>
    <ul>
        <li>📊 <b>Dashboard</b> (Monitoring Utama & Grafik)</li>
        <li>🔴 <b>Input Part NG</b> (Pencatatan Part Rusak)</li>
        <li>🛠️ <b>Team Repair</b> (Manajemen Tim Perbaikan)</li>
        <li>🟢 <b>Install Mesin</b> (Pemasangan & Setup Mesin)</li>
    </ul>
</div>
""", unsafe_allow_html=True)
