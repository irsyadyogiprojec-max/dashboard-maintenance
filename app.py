import streamlit as st

st.set_page_config(
    page_title="Executive Maintenance System",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0B0F19 0%, #111827 50%, #0F172A 100%);
        color: #F3F4F6;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Executive Maintenance & OEE System")
st.markdown("---")
st.success("✅ Aplikasi berhasil berjalan dengan sistem Multi-Page!")
st.info("👉 Silakan gunakan menu navigasi di **Sidebar sebelah kiri** untuk berpindah antar halaman (Dashboard, Input Part NG, Team Repair, dan Install Mesin). Setiap halaman sudah memiliki link URL uniknya masing-masing!")
