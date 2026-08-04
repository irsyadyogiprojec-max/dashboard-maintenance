import streamlit as st

st.set_page_config(
    page_title="Executive Maintenance & OEE System",
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
st.caption("Klik tombol menu di bawah untuk membuka halaman spesifik dan mengambil link URL-nya untuk QR Code:")
st.markdown("---")

# Menggunakan pemanggilan path halaman yang kompatibel dengan server Streamlit terbaru
col1, col2 = st.columns(2)

with col1:
    st.page_link("pages/1_Dashboard.py", label="📊 Buka Halaman Dashboard", icon="📊")
    st.page_link("pages/2_Input_Part_NG.py", label="🔴 Buka Halaman Input Part NG", icon="🔴")

with col2:
    st.page_link("pages/3_Team_Repair.py", label="🛠️ Buka Halaman Team Repair", icon="🛠️")
    st.page_link("pages/4_Install_Mesin.py", label="🟢 Buka Halaman Install ke Mesin", icon="🟢")
