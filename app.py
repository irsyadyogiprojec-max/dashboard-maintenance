import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import random
import os

# ==========================================
# 1. KONFIGURASI HALAMAN & TEMA MEWAH (FUTURISTIC)
# ==========================================
st.set_page_config(
    page_title="Executive Maintenance & OEE Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk efek Glassmorphism & Neon Luxury
st.markdown("""
<style>
    /* Background Utama */
    .stApp {
        background: linear-gradient(135deg, #0B0F19 0%, #111827 50%, #0F172A 100%);
        color: #F3F4F6;
    }
    
    /* Styling Sidebar Mewah */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.85) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
    }

    /* Kartu Metrik dengan Efek Glassmorphism & Neon Border */
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        border-radius: 16px !important;
        padding: 18px 22px !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px 0 rgba(56, 189, 248, 0.25);
        border: 1px solid rgba(56, 189, 248, 0.5) !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 30px !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #38BDF8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        color: #94A3B8 !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
    }

    /* Form Container dengan Efek Kaca */
    [data-testid="stForm"] {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 25px !important;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    /* Tombol Simpan Bergradasi Neon */
    .stButton>button, div[data-testid="stFormSubmitButton"]>button {
        background: linear-gradient(90deg, #2563EB 0%, #7C3AED 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 12px 28px !important;
        box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover, div[data-testid="stFormSubmitButton"]>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 28px rgba(124, 58, 237, 0.7) !important;
    }

    hr { border-color: rgba(255, 255, 255, 0.08) !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATASET IN-MEMORY & KOORDINAT MESIN
# ==========================================
if "maintenance_data" not in st.session_state:
    st.session_state["maintenance_data"] = pd.DataFrame([
        {"Tanggal": "2026-08-01", "Mesin": "QC 01", "Kategori": "Repair", "Status_Part": "Part Ready", "No_Seri": "SN-88231", "Nama_Part": "Valve Hydro", "Qty": 0, "Teknisi": "Andi"},
        {"Tanggal": "2026-08-02", "Mesin": "ISP-017", "Kategori": "Part Replacement", "Status_Part": "Part NG", "No_Seri": "SN-10492", "Nama_Part": "Bearing SKF 6204", "Qty": 2, "Teknisi": "Budi"},
        {"Tanggal": "2026-08-03", "Mesin": "QC 02", "Kategori": "Repair", "Status_Part": "Part Repair", "No_Seri": "SN-55410", "Nama_Part": "Motor Shaft", "Qty": 1, "Teknisi": "Candra"}
    ])

MACHINE_POSITIONS = {
    "CRANK SHAFT LINE": {"x": 500, "y": 880, "line": "Crank Shaft"},
    "QC 01": {"x": 200, "y": 800, "line": "Crank Shaft"},
    "ISP-017": {"x": 130, "y": 800, "line": "Crank Shaft"},
    "QC 02": {"x": 300, "y": 800, "line": "Crank Shaft"},
    "CYLINDER HEAD LINE": {"x": 500, "y": 620, "line": "Cyl Head"},
    "CAM SHAFT LINE": {"x": 250, "y": 380, "line": "Cam Shaft"},
    "QC 1": {"x": 308, "y": 320, "line": "Cam Shaft"},
    "CYLINDER BLOCK LINE": {"x": 480, "y": 120, "line": "Cyl Block"},
    "Pos QC": {"x": 100, "y": 60, "line": "Cyl Block"}
}

MACHINE_LIST = list(MACHINE_POSITIONS.keys()) + ["Mesin Lainnya"]

# ==========================================
# 3. NAVIGASI BAR
# ==========================================
query_params = st.query_params
default_page_index = 0

if "page" in query_params:
    param_val = query_params["page"]
    if param_val == "input_ng":
        default_page_index = 1
    elif param_val == "input_repair":
        default_page_index = 2
    elif param_val == "input_ready":
        default_page_index = 3

st.sidebar.markdown("## ⚡ Executive Control")
menu_options = [
    "📊 Executive Dashboard", 
    "🔴 Form Input Part NG", 
    "🛠️ Form Input Part Repair", 
    "🟢 Form Input Part Ready"
]

page = st.sidebar.radio("Pilih Modul:", menu_options, index=default_page_index)
df = st.session_state["maintenance_data"]

# ==========================================
# 4. FUNGSI RENDER FORM INPUT (TANPA DOWNTIME)
# ==========================================
def render_input_form(status_part_default, kategori_default, title_text, color_tag):
    st.title(f"{color_tag} {title_text}")
    st.caption(f"Halaman Khusus Scan & Input untuk Kategori **{status_part_default}**.")
    
    uploaded_file = st.file_uploader("📷 Upload Foto Part / Label Seri", type=["png", "jpg", "jpeg"], key=f"file_{status_part_default}")
    
    scanned_sn = ""
    scanned_name = ""

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Foto Part Diunggah", width=180)
        
        with st.spinner("🔍 Memindai Gambar & Deteksi Nomor Seri/Nama Part..."):
            scanned_sn = f"SN-{random.randint(10000, 99999)}"
            parts_dummy = ["Bearing SKF 6204", "Seal Hydraulic", "V-Belt B-52", "Sensor Proximity", "Valve Hydro"]
            scanned_name = random.choice(parts_dummy)
        st.success("✅ Auto-Scan Berhasil! Nomor Seri dan Nama Part terisi otomatis.")

    with st.form(f"form_{status_part_default}", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            tanggal = st.date_input("Tanggal Perbaikan")
            mesin = st.selectbox("Pilih Mesin / Lokasi Stasiun", MACHINE_LIST)
            no_seri = st.text_input("Nomor Seri Part (Auto-Generated)", value=scanned_sn)
            nama_part = st.text_input("Nama Sparepart (Auto-Generated)", value=scanned_name)

        with col_b:
            qty = st.number_input("Jumlah Part (Qty)", min_value=1, value=1)
            teknisi = st.text_input("Nama Teknisi / PIC")

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(f"💾 Simpan Laporan ({status_part_default})")

        if submitted:
            new_data = {
                "Tanggal": str(tanggal),
                "Mesin": mesin,
                "Kategori": kategori_default,
                "Status_Part": status_part_default,
                "No_Seri": no_seri if no_seri else "-",
                "Nama_Part": nama_part if nama_part else "-",
                "Qty": qty,
                "Teknisi": teknisi
            }
            st.session_state["maintenance_data"] = pd.concat(
                [st.session_state["maintenance_data"], pd.DataFrame([new_data])], 
                ignore_index=True
            )
            st.success(f"✨ Data {status_part_default} untuk {mesin} berhasil disimpan!")

# ==========================================
# 5. HALAMAN UTAMA DASHBOARD
# ==========================================
if page == "📊 Executive Dashboard":
    st.title("🛡️ Executive Maintenance & OEE Dashboard")
    st.caption("Pemantauan Performa Mesin, Log Perbaikan, dan Interactive Plant Layout Map")
    st.markdown("---")

    # Ringkasan Kartu Metrik
    col1, col2, col3, col4 = st.columns(4)
    
    total_repair = len(df[df["Kategori"] == "Repair"]) if not df.empty else 0
    total_replace = len(df[df["Kategori"] == "Part Replacement"]) if not df.empty else 0
    part_ng = len(df[df["Status_Part"] == "Part NG"]) if not df.empty else 0

    col1.metric("🛠️ Total Repair", f"{total_repair} Pekerjaan")
    col2.metric("🔄 Part Replace", f"{total_replace} Pekerjaan")
    col3.metric("⚠️ Part NG", f"{part_ng} Item")
    col4.metric("📈 OEE Keseluruhan", "84.2%", delta="1.7% MoM")

    st.markdown("---")

    # BAR CHART & PIE CHART MEWAH
    col_left, col_right = st.columns(2)
    chart_bg = "rgba(15, 23, 42, 0.0)"
    font_color = "#F8FAFC"

    with col_left:
        st.subheader("📊 Volume Perbaikan berdasarkan Kategori")
        if not df.empty:
            cat_counts = df["Kategori"].value_counts().reset_index()
            cat_counts.columns = ["Kategori", "Jumlah"]
            
            fig_bar = px.bar(cat_counts, x="Kategori", y="Jumlah", text="Jumlah")
            fig_bar.update_traces(
                marker=dict(color="#38BDF8", line=dict(color="#0284C7", width=1.5)),
                textposition="outside", 
                textfont=dict(size=14, color=font_color)
            )
            fig_bar.update_layout(
                plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, font=dict(color=font_color),
                xaxis=dict(title="", showgrid=False),
                yaxis=dict(title="Jumlah Kejadian", showgrid=True, gridcolor="rgba(255,255,255,0.08)", zeroline=False),
                showlegend=False, height=340, margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("🧩 Breakdown Status Sparepart")
        if not df.empty:
            status_counts = df["Status_Part"].value_counts().reset_index()
            status_counts.columns = ["Status_Part", "Jumlah"]
            
            fig_pie = px.pie(status_counts, names="Status_Part", values="Jumlah", hole=0.6)
            fig_pie.update_traces(
                textinfo="percent+label", textfont=dict(size=12, color="#FFFFFF"),
                marker=dict(colors=["#FF0055", "#00F5D4", "#FFB703"])
            )
            fig_pie.update_layout(
                plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, font=dict(color=font_color),
                height=340, margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # TABEL LOG RIWAYAT MAINTENANCE
    st.subheader("📋 Log Riwayat Maintenance Terakhir")
    st.dataframe(df, use_container_width=True)

    st.markdown("---")

    # ==========================================
    # MAP LAYOUT PABRIK INTERAKTIF MEWAH
    # ==========================================
    st.subheader("🗺️ Plant Layout Map & Indikator Lampu Real-Time")
    st.caption("Titik lampu interaktif dengan pendaran cahaya neon (glow effect).")

    latest_status = {}
    if not df.empty:
        for idx, row in df.iterrows():
            latest_status[row["Mesin"]] = row["Status_Part"]

    fig_map = go.Figure()

    folder_saat_ini = os.path.dirname(os.path.abspath(__file__))
    pilihan_nama_file = ["layout.png", "layout.PNG", "layout.png.png", "layout.png.", "layout"]
    jalur_gambar = None

    for nama in pilihan_nama_file:
        cek_jalur = os.path.join(folder_saat_ini, nama)
        if os.path.exists(cek_jalur):
            jalur_gambar = cek_jalur
            break

    if jalur_gambar and os.path.exists(jalur_gambar):
        img = Image.open(jalur_gambar)
        img_width, img_height = img.size

        fig_map.add_layout_image(
            dict(
                source=img,
                xref="x",
                yref="y",
                x=0,
                y=img_height,
                sizex=img_width,
                sizey=img_height,
                sizing="stretch",
                opacity=1.0,
                layer="below"
            )
        )
    else:
        st.warning("⚠️ File gambar layout tidak ditemukan.")
        img_width, img_height = 1000, 1000

    for machine_name, pos in MACHINE_POSITIONS.items():
        status = latest_status.get(machine_name, "Normal")
        
        if status == "Part NG":
            color_main = "#FF0055"      # 🔴 Merah Neon
            color_glow = "rgba(255, 0, 85, 0.4)"
            label_status = "Part NG (Breakdown)"
        elif status == "Part Repair":
            color_main = "#FFB703"      # 🟡 Kuning Neon
            color_glow = "rgba(255, 183, 3, 0.4)"
            label_status = "Part Repair (Dalam Perbaikan)"
        elif status == "Part Ready":
            color_main = "#00F5D4"      # 🟢 Cyan Neon
            color_glow = "rgba(0, 245, 212, 0.4)"
            label_status = "Part Ready (Siap Beroperasi)"
        else:
            color_main = "#10B981"      # 🟢 Hijau Emerald
            color_glow = "rgba(16, 185, 129, 0.35)"
            label_status = "Normal (Berjalan)"

        # 1. GLOW EFFECT (OUTER HALO)
        fig_map.add_trace(go.Scatter(
            x=[pos["x"]],
            y=[pos["y"]],
            mode="markers",
            hoverinfo="skip",
            showlegend=False,
            marker=dict(
                size=44,
                color=color_glow,
                line=dict(width=0)
            )
        ))

        # 2. LAMPU INTI & TEKS HITAM
        fig_map.add_trace(go.Scatter(
            x=[pos["x"]],
            y=[pos["y"]],
            mode="markers+text",
            name=machine_name,
            text=[f" <b>{machine_name}</b> "],
            textposition="top center",
            textfont=dict(color="#000000", size=11, family="Arial, sans-serif"),
            marker=dict(
                size=22,
                color=color_main,
                symbol="circle",
                line=dict(width=2.5, color="#FFFFFF"),
                opacity=1.0
            ),
            hoverinfo="text",
            hovertext=f"<b>Mesin/Stasiun:</b> {machine_name}<br><b>Area Lini:</b> {pos['line']}<br><b>Status Terkini:</b> {label_status}"
        ))

    fig_map.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, img_width]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, img_height]),
        plot_bgcolor="#0F172A",
        paper_bgcolor="#1E293B",
        height=850,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10)
    )

    st.plotly_chart(fig_map, use_container_width=True)

elif page == "🔴 Form Input Part NG":
    render_input_form("Part NG", "Part Replacement", "Form Laporan Kerusakan Part (Part NG)", "🔴")

elif page == "🛠️ Form Input Part Repair":
    render_input_form("Part Repair", "Repair", "Form Laporan Perbaikan Part (Part Repair)", "🛠️")

elif page == "🟢 Form Input Part Ready":
    render_input_form("Part Ready", "Part Replacement", "Form Laporan Part Ready to Use", "🟢")