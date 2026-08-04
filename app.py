import streamlit as st
import pandas as pd
import numpy as np

# 1. Konfigurasi Halaman & Membuka Sidebar Otomatis
st.set_page_config(
    page_title="Executive Maintenance & OEE System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"  # Membuat sidebar terbuka secara otomatis
)

# 2. Custom CSS untuk Styling ala Dashboard Profesional
st.markdown("""
<style>
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
    }
    .metric-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# 3. Header Utama
st.title("📊 EXECUTIVE DASHBOARD & OEE SYSTEM")
st.caption("March, 15 2026 | Real-time Monitoring Pabrik")
st.markdown("---")

# 4. Bagian Baris 1: Metric Cards (3 Kolom Atas)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="metric-card">
        <p style="color: #64748B; margin-bottom: 0px;">Lorem Ipsum</p>
        <h2 style="color: #10B981; margin-top: 0px;">▲ 500%</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <p style="color: #64748B; margin-bottom: 0px;">Lorem Ipsum</p>
        <h2 style="color: #EF4444; margin-top: 0px;">▼ 120%</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <p style="color: #64748B; margin-bottom: 0px;">Lorem Ipsum</p>
        <h2 style="color: #10B981; margin-top: 0px;">+ 350%</h2>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# 5. Bagian Baris 2: Progress Bars (4 Kolom Target)
col4, col5, col6, col7 = st.columns(4)
with col4:
    st.text("Lorem Ipsum (65%)")
    st.progress(0.65)
with col5:
    st.text("Lorem Ipsum (65%)")
    st.progress(0.65)
with col6:
    st.text("Lorem Ipsum (65%)")
    st.progress(0.65)
with col7:
    st.text("Lorem Ipsum (65%)")
    st.progress(0.65)

st.markdown("---")

# 6. Bagian Baris 3: Grafik Batang, Pie Chart, & Line Chart
chart_col1, chart_col2, chart_col3 = st.columns(3)

# Data Dummy untuk Grafik
chart_data = pd.DataFrame(
    np.random.randn(10, 2),
    columns=['Lorem A', 'Lorem B']
)

pie_data = pd.DataFrame({
    'Kategori': ['Kategori A', 'Kategori B', 'Kategori C'],
    'Val': [20, 25, 55]
}).set_index('Kategori')

line_data = pd.DataFrame(
    np.random.randn(10, 1),
    columns=['Trend']
)

with chart_col1:
    st.subheader("Lorem Ipsum")
    st.bar_chart(chart_data)

with chart_col2:
    st.subheader("Lorem Ipsum (Pie)")
    # Menggunakan bar/area chart atau dataframe custom jika ingin representasi pie proporsi
    st.dataframe(pie_data, use_container_width=True)
    st.caption("Distribusi Persentase: 20% | 25% | 55%")

with chart_col3:
    st.subheader("Lorem Ipsum")
    st.line_chart(line_data)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #94A3B8;'>Lorem Ipsum Is Simply Dummy Text</p>", unsafe_allow_html=True)
