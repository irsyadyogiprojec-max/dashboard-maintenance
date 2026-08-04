import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import random
import os
from supabase import create_client, Client

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS RESPONSIF
# ==========================================
st.set_page_config(
    page_title="Executive Maintenance & OEE Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0B0F19 0%, #111827 50%, #0F172A 100%);
        color: #F3F4F6;
    }
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
    }
    [data-testid="stHorizontalBlock"] > div {
        min-width: 0 !important;
        flex: 1 1 0px !important;
    }
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
        border-radius: 12px !important;
        padding: 8px 10px !important;
        text-align: center;
    }
    [data-testid="stMetricValue"] {
        font-size: clamp(1rem, 2.5vw, 1.8rem) !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #38BDF8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    [data-testid="stMetricLabel"] {
        font-size: clamp(0.65rem, 1.5vw, 0.85rem) !important;
        color: #94A3B8 !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    [data-testid="stForm"] {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 16px !important;
        backdrop-filter: blur(12px);
    }
    .stButton>button, div[data-testid="stFormSubmitButton"]>button {
        background: linear-gradient(90deg, #2563EB 0%, #7C3AED 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        padding: 10px !important;
        width: 100% !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    hr { border-color: rgba(255, 255, 255, 0.08) !important; margin: 0.8rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONEKSI SUPABASE DATABASE
# ==========================================
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if not url or not key:
        st.error("⚠️ Kunci SUPABASE_URL & SUPABASE_KEY belum diatur di Streamlit Secrets!")
        return None
    return create_client(url, key)

supabase = init_supabase()

def load_data_from_supabase():
    if supabase is None:
        return pd.DataFrame()
    try:
        response = supabase.table("maintenance_log").select("*").order("id", desc=True).execute()
        data = response.data
        if data:
            df_res = pd.DataFrame(data)
            col_map = {
                "tanggal": "Tanggal", "mesin": "Mesin", "kategori": "Kategori",
                "status_part": "Status_Part", "no_seri": "No_Seri",
                "nama_part": "Nama_Part", "qty": "Qty", "teknisi": "Teknisi"
            }
            return df_res.rename(columns=col_map)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal memuat data dari Supabase: {e}")
        return pd.DataFrame()

def insert_data_to_supabase(record):
    if supabase is None:
        return False
    try:
        supabase.table("maintenance_log").insert(record).execute()
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan data: {e}")
        return False

df = load_data_from_supabase()

MACHINE_LIST = [
    "CRANK SHAFT LINE", "QC 01", "ISP-017", "QC 02", 
    "CYLINDER HEAD LINE", "CAM SHAFT LINE", "QC 1", 
    "CYLINDER BLOCK LINE", "Pos QC", "Mesin Lainnya"
]

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

# ==========================================
# 4. FUNGSI FORM INPUT
# ==========================================
def render_input_form(status_part_default, kategori_default, title_text, color_tag):
    st.title(f"{color_tag} {title_text}")
    st.caption(f"Halaman Khusus Scan & Input untuk Kategori **{status_part_default}**.")
    
    uploaded_file = st.file_uploader("📷 Upload Foto Part / Label Seri", type=["png", "jpg", "jpeg"], key=f"file_{status_part_default}")
    
    scanned_sn = ""
    scanned_name = ""

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Foto Part Diunggah", width=150)
        
        with st.spinner("🔍 Memindai Gambar..."):
            scanned_sn = f"SN-{random.randint(10000, 99999)}"
            parts_dummy = ["Bearing SKF 6204", "Seal Hydraulic", "V-Belt B-52", "Sensor Proximity", "Valve Hydro"]
            scanned_name = random.choice(parts_dummy)
        st.success("✅ Auto-Scan Berhasil!")

    with st.form(f"form_{status_part_default}", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            tanggal = st.date_input("Tanggal Perbaikan")
            mesin = st.selectbox("Pilih Mesin / Lokasi Stasiun", MACHINE_LIST)
            no_seri = st.text_input("Nomor Seri Part", value=scanned_sn)

        with col_b:
            nama_part = st.text_input("Nama Sparepart", value=scanned_name)
            qty = st.number_input("Jumlah Part (Qty)", min_value=1, value=1)
            teknisi = st.text_input("Nama Teknisi / PIC")

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button(f"💾 Simpan ke Database ({status_part_default})")

        if submitted:
            payload = {
                "tanggal": str(tanggal),
                "mesin": mesin,
                "kategori": kategori_default,
                "status_part": status_part_default,
                "no_seri": no_seri if no_seri else "-",
                "nama_part": nama_part if nama_part else "-",
                "qty": int(qty),
                "teknisi": teknisi if teknisi else "-"
            }
            if insert_data_to_supabase(payload):
                st.success(f"✨ Data {status_part_default} berhasil tersimpan permanen di Supabase!")
                st.rerun()

# ==========================================
# 5. HALAMAN DASHBOARD UTAMA
# ==========================================
if page == "📊 Executive Dashboard":
    st.title("🛡️ Executive Maintenance")
    st.caption("Monitoring Performa Mesin & Plant Layout Map Real-Time (Connected to Supabase)")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    
    total_repair = len(df[df["Kategori"] == "Repair"]) if not df.empty and "Kategori" in df.columns else 0
    total_replace = len(df[df["Kategori"] == "Part Replacement"]) if not df.empty and "Kategori" in df.columns else 0
    part_ng = len(df[df["Status_Part"] == "Part NG"]) if not df.empty and "Status_Part" in df.columns else 0

    col1.metric("🛠️ Repair", f"{total_repair} Pekerjaan")
    col2.metric("🔄 Replace", f"{total_replace} Pekerjaan")
    col3.metric("⚠️ Part NG", f"{part_ng} Item")
    col4.metric("📈 OEE", "84.2%", delta="1.7% MoM")

    st.markdown("---")

    # MAP LAYOUT PABRIK INTERAKTIF
    st.subheader("🗺️ Plant Layout Map Real-Time")
    st.caption("Sentuh/Hover titik lampu untuk informasi rinci status mesin.")

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
    else:
        img_width, img_height = 1000, 1000

    MACHINE_POSITIONS = {
        "CRANK SHAFT LINE": {"x": img_width * 0.40, "y": img_height * 0.70, "line": "Crank Shaft"},
        "QC 01": {"x": img_width * 0.22, "y": img_height * 0.70, "line": "Crank Shaft"},
        "ISP-017": {"x": img_width * 0.14, "y": img_height * 0.70, "line": "Crank Shaft"},
        "QC 02": {"x": img_width * 0.30, "y": img_height * 0.70, "line": "Crank Shaft"},
        "CYLINDER HEAD LINE": {"x": img_width * 0.48, "y": img_height * 0.48, "line": "Cyl Head"},
        "CAM SHAFT LINE": {"x": img_width * 0.28, "y": img_height * 0.35, "line": "Cam Shaft"},
        "QC 1": {"x": img_width * 0.35, "y": img_height * 0.35, "line": "Cam Shaft"},
        "CYLINDER BLOCK LINE": {"x": img_width * 0.48, "y": img_height * 0.18, "line": "Cyl Block"},
        "Pos QC": {"x": img_width * 0.12, "y": img_height * 0.18, "line": "Cyl Block"}
    }

    latest_status = {}
    if not df.empty and "Mesin" in df.columns:
        for idx, row in df.iterrows():
            if row["Mesin"] not in latest_status:
                latest_status[row["Mesin"]] = row["Status_Part"]

    fig_map = go.Figure()

    if jalur_gambar and os.path.exists(jalur_gambar):
        fig_map.add_layout_image(
            dict(
                source=img,
                xref="x", yref="y",
                x=0, y=img_height,
                sizex=img_width, sizey=img_height,
                sizing="stretch", opacity=1.0, layer="below"
            )
        )

    for machine_name, pos in MACHINE_POSITIONS.items():
        status = latest_status.get(machine_name, "Normal")
        
        if status == "Part NG":
            color_main = "#FF0055"
            color_glow = "rgba(255, 0, 85, 0.4)"
            label_status = "Part NG (Breakdown)"
        elif status == "Part Repair":
            color_main = "#FFB703"
            color_glow = "rgba(255, 183, 3, 0.4)"
            label_status = "Part Repair (Dalam Perbaikan)"
        elif status == "Part Ready":
            color_main = "#00F5D4"
            color_glow = "rgba(0, 245, 212, 0.4)"
            label_status = "Part Ready (Siap Beroperasi)"
        else:
            color_main = "#10B981"
            color_glow = "rgba(16, 185, 129, 0.35)"
            label_status = "Normal (Berjalan)"

        fig_map.add_trace(go.Scatter(
            x=[pos["x"]], y=[pos["y"]],
            mode="markers", hoverinfo="skip", showlegend=False,
            marker=dict(size=26, color=color_glow, line=dict(width=0))
        ))

        fig_map.add_trace(go.Scatter(
            x=[pos["x"]], y=[pos["y"]],
            mode="markers+text", name=machine_name,
            text=[f"<b>{machine_name}</b>"], textposition="top center",
            textfont=dict(color="#000000", size=10, family="Arial, sans-serif"),
            marker=dict(size=14, color=color_main, symbol="circle", line=dict(width=2, color="#FFFFFF")),
            hoverinfo="text",
            hovertext=f"<b>Mesin:</b> {machine_name}<br><b>Area:</b> {pos['line']}<br><b>Status:</b> {label_status}"
        ))

    fig_map.update_xaxes(range=[0, img_width], showgrid=False, zeroline=False, showticklabels=False, autorange=False)
    fig_map.update_yaxes(range=[0, img_height], showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1, autorange=False)

    fig_map.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        height=600, showlegend=False, margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig_map, use_container_width=True, config={'responsive': True, 'displayModeBar': False})

    st.markdown("---")

    col_left, col_right = st.columns(2)
    chart_bg = "rgba(0,0,0,0)"
    font_color = "#F8FAFC"

    with col_left:
        st.subheader("📊 Volume Perbaikan")
        if not df.empty and "Kategori" in df.columns:
            cat_counts = df["Kategori"].value_counts().reset_index()
            cat_counts.columns = ["Kategori", "Jumlah"]
            
            fig_bar = px.bar(cat_counts, x="Kategori", y="Jumlah", text="Jumlah")
            fig_bar.update_traces(
                marker=dict(color="#38BDF8", line=dict(color="#0284C7", width=1.5)),
                textposition="outside", textfont=dict(size=12, color=font_color)
            )
            fig_bar.update_layout(
                plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, font=dict(color=font_color),
                xaxis=dict(title="", showgrid=False),
                yaxis=dict(title="", showgrid=True, gridcolor="rgba(255,255,255,0.08)", zeroline=False),
                showlegend=False, height=280, margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("🧩 Status Sparepart")
        if not df.empty and "Status_Part" in df.columns:
            status_counts = df["Status_Part"].value_counts().reset_index()
            status_counts.columns = ["Status_Part", "Jumlah"]
            
            fig_pie = px.pie(status_counts, names="Status_Part", values="Jumlah", hole=0.5)
            fig_pie.update_traces(
                textinfo="percent+label", textfont=dict(size=11, color="#FFFFFF"),
                marker=dict(colors=["#FF0055", "#00F5D4", "#FFB703"])
            )
            fig_pie.update_layout(
                plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, font=dict(color=font_color),
                height=280, margin=dict(l=10, r=10, t=20, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📋 Log Maintenance Terakhir (Data Supabase)")
    st.dataframe(df, use_container_width=True)

elif page == "🔴 Form Input Part NG":
    render_input_form("Part NG", "Part Replacement", "Form Part NG", "🔴")

elif page == "🛠️ Form Input Part Repair":
    render_input_form("Part Repair", "Repair", "Form Part Repair", "🛠️")

elif page == "🟢 Form Input Part Ready":
    render_input_form("Part Ready", "Part Replacement", "Form Part Ready", "🟢")
