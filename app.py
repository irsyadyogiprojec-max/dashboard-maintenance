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
st.caption("Pilih menu di bawah atau melalui sidebar untuk membuka halaman spesifik dengan URL unik.")
st.markdown("---")

# Menggunakan path langsung tanpa ekstensi .py agar tidak terjadi KeyError
st.page_link("pages/1_Dashboard.py", label="📊 Buka Halaman Dashboard", icon="📊")
st.page_link("pages/2_Input_Part_NG.py", label="🔴 Buka Halaman Input Part NG", icon="🔴")
st.page_link("pages/3_Team_Repair.py", label="🛠️ Buka Halaman Team Repair", icon="🛠️")
st.page_link("pages/4_Install_Mesin.py", label="🟢 Buka Halaman Install ke Mesin", icon="🟢")
