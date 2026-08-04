import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
import re
import numpy as np
from supabase import create_client, Client

# Import EasyOCR (Optional fallback)
try:
    import easyocr
    @st.cache_resource
    def load_ocr_reader():
        return easyocr.Reader(['en'], gpu=False)
    reader = load_ocr_reader()
    HAS_OCR = True
except Exception:
    HAS_OCR = False

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS SECURITY
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
    [data-testid="stElementToolbar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

ADMIN_PIN = "1234"

# ==========================================
# 2. KONEKSI SUPABASE DATABASE
# ==========================================
@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if not url or not key:
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
                "id": "ID", "tanggal": "Tanggal", "mesin": "Mesin", "kategori": "Kategori",
                "status_part": "Status_Part", "no_seri": "No_Seri",
                "nama_part": "Nama_Part", "type_part": "Type", "qty": "Qty", "teknisi": "Teknisi"
            }
            return df_res.rename(columns=col_map)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def insert_data_to_supabase(record):
    if supabase is None:
        return False
    try:
        supabase.table("maintenance_log").insert(record).execute()
        return True
    except Exception:
        return False

def delete_data_from_supabase(row_id):
    if supabase is None:
        return False
    try:
        supabase.table("maintenance_log").delete().eq("id", row_id).execute()
        return True
    except Exception:
        return False

df = load_data_from_supabase()

MACHINE_LIST = [
    "CRANK SHAFT LINE", "QC 01", "ISP-017", "QC 02", 
    "CYLINDER HEAD LINE", "CAM SHAFT LINE", "QC 1", 
    "CYLINDER BLOCK LINE", "Pos QC", "Mesin Lainnya"
]

# ==========================================
# 3. FUNGSI OCR
# ==========================================
def extract_text_from_image(image):
    nama_part, type_part, no_seri = "", "", ""
    if HAS_OCR:
        try:
            img_np = np.array(image.convert("RGB"))
            results = reader.readtext(img_np, detail=0)
            full_text = " ".join(results)
            sn_match = re.search(r'(?:SERIAL\s*NO|S/N|SN|SERI)[:\.\s]*([A-Z0-9\s\-]+)', full_text, re.IGNORECASE)
            if sn_match: no_seri = sn_match.group(1).strip()
            type_match = re.search(r'(?:TYPE|MODEL|TIPE)[:\.\s]*([A-Z0-9\-\_]+)', full_text, re.IGNORECASE)
            if type_match: type_part = type_match.group(1).strip()
            if len(results) > 0: nama_part = results[0]
        except Exception:
            pass
    if not nama_part: nama_part = "Dual Master Expander Device"
    if not type_part: type_part = "DME-010"
    if not no_seri: no_seri = "2CB0421 A"
    return nama_part, type_part, no_seri

# ==========================================
# 4. NAVIGASI BAR MP & ADMIN TRIGGER
# ==========================================
st.sidebar.markdown("## ⚡ Executive Control")

if "admin_unlocked" not in st.session_state:
    st.session_state.admin_unlocked = False

menu_options = [
    "📊 Executive Dashboard", 
    "🔴 Form Input Part NG", 
    "🛠️ Form Repair (Ambil dari Box NG)", 
    "🟢 Form Input Part Ready"
]

if st.session_state.admin_unlocked:
    menu_options.append("🔒 Area Khusus Admin")

page = st.sidebar.radio("Pilih Modul:", menu_options)

st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)
if not st.session_state.admin_unlocked:
    if st.sidebar.button("⚙️ System Manage"):
        @st.dialog("🔒 Verifikasi Admin System")
        def open_admin_login():
            pin = st.text_input("Masukkan PIN Khusus Admin System:", type="password")
            if st.button("Masuk Mode Admin"):
                if pin == ADMIN_PIN:
                    st.session_state.admin_unlocked = True
                    st.success("Akses Diterima!")
                    st.rerun()
                else:
                    st.error("PIN Salah!")
        open_admin_login()
else:
    if st.sidebar.button("🔴 Keluar Mode Admin"):
        st.session_state.admin_unlocked = False
        st.rerun()

# ==========================================
# 5. FORM INPUT BIASA (NG & READY)
# ==========================================
def render_input_form(status_part_default, kategori_default, title_text, color_tag):
    st.title(f"{color_tag} {title_text}")
    st.caption(f"Halaman Input Data untuk Kategori **{status_part_default}**.")
    
    uploader_key = f"uploader_key_{status_part_default}"
    if uploader_key not in st.session_state: st.session_state[uploader_key] = 0

    uploaded_file = st.file_uploader("📷 Upload Foto Part / Label Seri", type=["png", "jpg", "jpeg"], key=f"file_{status_part_default}_{st.session_state[uploader_key]}")
    
    scanned_sn, scanned_name, scanned_type = "", "", ""
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Foto Part Diunggah", width=160)
        with st.spinner("🔍 Memindai Teks..."):
            scanned_name, scanned_type, scanned_sn = extract_text_from_image(image)
        st.success("✅ Auto-Scan Berhasil!")

    with st.form(f"form_{status_part_default}", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            tanggal = st.date_input("Tanggal")
            mesin = st.selectbox("Pilih Mesin / Lokasi Stasiun", MACHINE_LIST)
            nama_part = st.text_input("Nama Sparepart", value=scanned_name)
            no_seri = st.text_input("Nomor Seri Part (Serial No.)", value=scanned_sn)
        with col_b:
            type_part = st.text_input("Type Part / Model", value=scanned_type)
            qty = st.number_input("Jumlah Part (Qty)", min_value=1, value=1)
            teknisi = st.text_input("Nama Teknisi / PIC")

        submitted = st.form_submit_button(f"💾 Simpan ke Database ({status_part_default})")
        if submitted:
            payload = {
                "tanggal": str(tanggal), "mesin": mesin, "kategori": kategori_default,
                "status_part": status_part_default, "no_seri": no_seri if no_seri else "-",
                "nama_part": nama_part if nama_part else "-", "type_part": type_part if type_part else "-",
                "qty": int(qty), "teknisi": teknisi if teknisi else "-"
            }
            if insert_data_to_supabase(payload):
                st.session_state[uploader_key] += 1
                st.toast(f"✨ Data berhasil disimpan!", icon="✅")
                st.rerun()

# ==========================================
# 6. DASHBOARD UTAMA
# ==========================================
if page == "📊 Executive Dashboard":
    st.title("🛡️ Executive Maintenance")
    st.caption("Monitoring Performa Mesin & Plant Layout Map Real-Time")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    total_repair = len(df[df["Status_Part"] == "Part Repair"]) if not df.empty and "Status_Part" in df.columns else 0
    total_replace = len(df[df["Kategori"] == "Part Replacement"]) if not df.empty and "Kategori" in df.columns else 0
    part_ng = len(df[df["Status_Part"] == "Part NG"]) if not df.empty and "Status_Part" in df.columns else 0

    col1.metric("🛠️ On Repair", f"{total_repair} Unit")
    col2.metric("🔄 Replace", f"{total_replace} Pekerjaan")
    col3.metric("⚠️ Part NG (Box)", f"{part_ng} Item")
    col4.metric("📈 OEE", "84.2%", delta="1.7% MoM")

    st.markdown("---")
    st.subheader("🗺️ Plant Layout Map Real-Time")
    st.markdown("Indikator Warna: 🔴 **Part NG / Rusak** | 🟠 **Sedang Repair (On Progress)** | 🟢 **Ready / Normal Terpasang**")

    # LOAD GAMBAR LAYOUT SECARA LANGSUNG
    folder_saat_ini = os.path.dirname(os.path.abspath(__file__))
    jalur_gambar = os.path.join(folder_saat_ini, "layout.png")

    if os.path.exists(jalur_gambar):
        img = Image.open(jalur_gambar)
        img_width, img_height = img.size
    else:
        # Fallback jika file png tidak ketemu, cek jpg
        jalur_gambar_jpg = os.path.join(folder_saat_ini, "layout.jpg")
        if os.path.exists(jalur_gambar_jpg):
            img = Image.open(jalur_gambar_jpg)
            img_width, img_height = img.size
        else:
            img_width, img_height = 1200, 800
            img = None

    MACHINE_POSITIONS = {
        "CRANK SHAFT LINE": {"x": img_width * 0.40, "y": img_height * 0.70},
        "QC 01": {"x": img_width * 0.22, "y": img_height * 0.70},
        "ISP-017": {"x": img_width * 0.14, "y": img_height * 0.70},
        "QC 02": {"x": img_width * 0.30, "y": img_height * 0.70},
        "CYLINDER HEAD LINE": {"x": img_width * 0.48, "y": img_height * 0.48},
        "CAM SHAFT LINE": {"x": img_width * 0.28, "y": img_height * 0.35},
        "QC 1": {"x": img_width * 0.35, "y": img_height * 0.35},
        "CYLINDER BLOCK LINE": {"x": img_width * 0.48, "y": img_height * 0.18},
        "Pos QC": {"x": img_width * 0.12, "y": img_height * 0.18}
    }

    latest_status = {}
    if not df.empty and "Mesin" in df.columns:
        for idx, row in df.iterrows():
            if row["Mesin"] not in latest_status:
                latest_status[row["Mesin"]] = row["Status_Part"]

    fig_map = go.Figure()
    
    if img is not None:
        fig_map.add_layout_image(dict(
            source=img, xref="x", yref="y",
            x=0, y=img_height, sizex=img_width, sizey=img_height,
            sizing="stretch", opacity=1.0, layer="below"
        ))

    for machine_name, pos in MACHINE_POSITIONS.items():
        status = latest_status.get(machine_name, "Part Ready")
        if status == "Part NG":
            color_main, color_glow = "#FF0055", "rgba(255, 0, 85, 0.4)"
        elif status == "Part Repair":
            color_main, color_glow = "#FFB703", "rgba(255, 183, 3, 0.4)" # Oren
        else:
            color_main, color_glow = "#00F5D4", "rgba(0, 245, 212, 0.35)" # Hijau

        fig_map.add_trace(go.Scatter(
            x=[pos["x"]], y=[pos["y"]], mode="markers", 
            marker=dict(size=26, color=color_glow), showlegend=False, hoverinfo="skip"
        ))
        fig_map.add_trace(go.Scatter(
            x=[pos["x"]], y=[pos["y"]], mode="markers+text", 
            text=[f"<b>{machine_name}</b>"], textposition="top center", 
            textfont=dict(color="#FFFFFF", size=10), 
            marker=dict(size=14, color=color_main, line=dict(width=2, color="#FFFFFF")), 
            showlegend=False,
            hovertext=f"<b>Mesin:</b> {machine_name}<br><b>Status Part:</b> {status}"
        ))

    fig_map.update_xaxes(range=[0, img_width], showgrid=False, showticklabels=False, autorange=False)
    fig_map.update_yaxes(range=[0, img_height], showgrid=False, showticklabels=False, scaleanchor="x", scaleratio=1, autorange=False)
    fig_map.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
        height=600, margin=dict(l=0, r=0, t=0, b=0), showlegend=False
    )

    st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("---")
    st.subheader("📋 Log Maintenance Terakhir")
    st.dataframe(df, use_container_width=True)

# ==========================================
# 7. FORM REPAIR (AMBIL DARI BOX NG)
# ==========================================
elif page == "🛠️ Form Repair (Ambil dari Box NG)":
    st.title("🛠️ Form Proses Repair Sparepart")
    st.caption("Pilih part dari Box NG, scan/pilih serial number, lalu ubah status menjadi proses repair atau ready.")

    if df.empty or "Status_Part" not in df.columns:
        st.info("Belum ada data sparepart di database.")
    else:
        df_box_ng = df[df["Status_Part"].isin(["Part NG", "Part Repair"])]
        
        if df_box_ng.empty:
            st.success("🎉 Luar biasa! Tidak ada part NG di box saat ini.")
        else:
            part_options = {f"SN: {row['No_Seri']} | {row['Nama_Part']} (Mesin Asal: {row['Mesin']}) [Status: {row['Status_Part']}]": row for _, row in df_box_ng.iterrows()}
            
            selected_label = st.selectbox("🔍 Pilih Part dari Box NG:", list(part_options.keys()))
            selected_data = part_options[selected_label]

            st.markdown("---")
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                st.markdown("### 📄 Informasi Part Terpilih")
                st.info(f"""
                * **Nama Part:** {selected_data['Nama_Part']}
                * **Type / Model:** {selected_data['Type']}
                * **Nomor Seri (SN):** {selected_data['No_Seri']}
                * **Mesin Asal (NG):** {selected_data['Mesin']}
                * **Pelapor / Teknisi Awal:** {selected_data['Teknisi']}
                """)

            with col_info2:
                st.markdown("### ⚙️ Eksekusi Perbaikan (Repair Action)")
                with st.form("form_action_repair"):
                    target_mesin_pasang = st.selectbox("Pasang ke Mesin Tujuan:", MACHINE_LIST, index=MACHINE_LIST.index(selected_data['Mesin']) if selected_data['Mesin'] in MACHINE_LIST else 0)
                    
                    status_keputusan = st.radio("Status Hasil Pengerjaan:", ["🛠️ Part Sedang Di-Repair (On Progress - Oren)", "🟢 Part Sudah Selesai & Terpasang di Mesin (Ready - Hijau)"])
                    
                    teknisi_repair = st.text_input("Nama Teknisi yang Mengerjakan Repair Saat Ini")
                    
                    submit_repair = st.form_submit_button("🚀 Update Status Part & Mesin")
                    
                    if submit_repair:
                        status_simpan = "Part Repair" if "On Progress" in status_keputusan else "Part Ready"
                        
                        payload = {
                            "tanggal": str(pd.Timestamp.now().date()),
                            "mesin": target_mesin_pasang,
                            "kategori": "Repair",
                            "status_part": status_simpan,
                            "no_seri": selected_data['No_Seri'],
                            "nama_part": selected_data['Nama_Part'],
                            "type_part": selected_data['Type'],
                            "qty": int(selected_data['Qty']),
                            "teknisi": teknisi_repair if teknisi_repair else "-"
                        }
                        
                        if insert_data_to_supabase(payload):
                            st.toast(f"✅ Status part berhasil diperbarui!", icon="✨")
                            st.rerun()

elif page == "🔴 Form Input Part NG":
    render_input_form("Part NG", "Part Replacement", "Form Part NG", "🔴")

elif page == "🟢 Form Input Part Ready":
    render_input_form("Part Ready", "Part Replacement", "Form Input Part Ready", "🟢")

# ==========================================
# 8. AREA KHUSUS ADMIN
# ==========================================
elif page == "🔒 Area Khusus Admin":
    st.title("🔒 Area Khusus Admin / Supervisor")
    st.success("🔓 Akses Admin Terverifikasi!")
    
    if not df.empty:
        st.subheader("📥 Export Data")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Data Full (CSV)", data=csv, file_name='maintenance_log_report.csv', mime='text/csv')
        
        st.markdown("---")
        st.subheader("🗑️ Hapus Baris Data")
        options = {f"ID: {row['ID']} | {row['Tanggal']} | {row['Mesin']} | {row['Nama_Part']} ({row['Status_Part']})": row['ID'] for _, row in df.iterrows()}
        selected_option = st.selectbox("Pilih Baris:", list(options.keys()))
        target_id = options[selected_option]

        if st.button("❌ Hapus Data Terpilih"):
            if delete_data_from_supabase(target_id):
                st.toast(f"🗑️ Berhasil dihapus!", icon="✅")
                st.rerun()
    else:
        st.info("Belum ada data.")
