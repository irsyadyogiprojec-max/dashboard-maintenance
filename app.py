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
    .menu-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 15px;
    }
    .menu-card a {
        color: #38BDF8;
        font-size: 18px;
        font-weight: bold;
        text-decoration: none;
    }
    .menu-card a:hover {
        text-decoration: underline;
        color: #7DD3FC;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ Executive Maintenance & OEE System")
st.caption("Pilih menu di bawah ini untuk berpindah halaman dan mengambil link URL-nya untuk QR Code:")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="menu-card">
        <h3>📊</h3>
        <a href="1_Dashboard" target="_self">Buka Halaman Dashboard</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="menu-card">
        <h3>🔴</h3>
        <a href="2_Input_Part_NG" target="_self">Buka Halaman Input Part NG</a>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="menu-card">
        <h3>🛠️</h3>
        <a href="3_Team_Repair" target="_self">Buka Halaman Team Repair</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="menu-card">
        <h3>🟢</h3>
        <a href="4_Install_Mesin" target="_self">Buka Halaman Install ke Mesin</a>
    </div>
    """, unsafe_allow_html=True)
