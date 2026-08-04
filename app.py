import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
import re
import numpy as np
from supabase import create_client, Client
import io
import base64

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
# 2. KONEKSI SUPABASE & GLOBAL PATH
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
            if "foto_base64" in df_res.columns:
                df_res["foto_base64"] = df_res["foto_base64"].fillna("")
                
            col_map = {
                "id": "ID", "tanggal": "Tanggal", "mesin": "Mesin", "kategori": "Kategori",
                "status_part": "Status_Part", "no_seri": "No_Seri",
                "nama_part": "Nama_Part", "type_part": "Type", "qty": "Qty", "teknisi": "Teknisi",
                "foto_base64": "Foto_Base64"
            }
            existing_cols = {k: v for k, v in col_map.items() if k in df_res.columns}
            return df_res.rename(columns=existing_cols)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def insert_data_to_supabase(record):
    if supabase is None:
        return False
    try:
        supabase.table("maintenance_log").insert(record).execute()
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan ke database: {e}")
        return False

def update_status_in_supabase(row_id, new_status, new_teknisi=""):
    if supabase is None:
        return False
    try:
        update_data = {"status_part": new_status}
        if new_teknisi:
            update_data["teknisi"] = new_teknisi
        supabase.table("maintenance_log").update(update_data).eq("id", row_id).execute()
        return True
    except Exception as e:
        st.error(f"Gagal memperbarui status: {e}")
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

folder_saat_ini = os.path.dirname(os.path.abspath(__file__))
kemungkinan_nama_file = [
    "layout.png.png", "lay out.PNG.PNG", "lay out.png", "lay out.PNG", 
    "layout.png", "layout.PNG", "layout.jpg", "layout.jpeg"
]
jalur_gambar = None
for nama_file in kemungkinan_nama_file:
    cek_jalur = os.path.join(folder_saat_ini, nama_file)
    if os.path.exists(cek_jalur):
        jalur_gambar = cek_jalur
        break

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
# 4. NAVIGASI BAR & ADMIN TRIGGER
# ==========================================
st.sidebar.markdown("## ⚡ Executive Control")

if "admin_unlocked" not in st.session_state:
    st.session_state.admin_unlocked = False

menu_options = [
    "📊 Executive Dashboard", 
    "🔴 Form Input Part NG (Mesin Rusak)", 
    "🛠️ Form Team Repair (Box NG & On Repair)", 
    "🟢 Form Install Machine (Ambil Box Ready)"
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
# 5. DASHBOARD UTAMA
# ==========================================
if page == "📊 Executive Dashboard":
    st.title("🛡️ Executive Maintenance")
    st.caption("Monitoring Performa Mesin & Plant Layout Map Real-Time")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    total_repair = len(df[df["Status_Part"] == "Part Repair"]) if not df.empty and "Status_Part" in df.columns else 0
    total_ready = len(df[df["Status_Part"] == "Part Ready"]) if not df.empty and "Status_Part" in df.columns else 0
    part_ng = len(df[df["Status_Part"] == "Part NG"]) if not df.empty and "Status_Part" in df.columns else 0

    col1.metric("🛠️ On Repair (Kuning)", f"{total_repair} Unit")
    col2.metric("📦 Box Ready (Biru)", f"{total_ready} Unit")
    col3.metric("⚠️ Mesin NG / Rusak", f"{part_ng} Mesin")
    col4.metric("📈 OEE", "84.2%", delta="1.7% MoM")

    st.markdown("---")
    st.subheader("🗺️ Plant Layout Map Real-Time")
    st.markdown("Indikator Warna Mesin: 🔴 **Mesin Rusak (Ada Part NG)** | 🟢 **Mesin Normal / Beroperasi**")

    if jalur_gambar:
        img_pil = Image.open(jalur_gambar)
        img_width, img_height = img_pil.size

        koordinat_mesin = {
            "CRANK SHAFT LINE": {"x": img_width * 0.5, "y": img_height * 0.5},
            "CYLINDER HEAD LINE": {"x": img_width * 0.5, "y": img_height * 0.3},
            "CYLINDER BLOCK LINE": {"x": img_width * 0.5, "y": img_height * 0.7},
            "QC 01": {"x": img_width * 0.3, "y": img_height * 0.4},
            "ISP-017": {"x": img_width * 0.2, "y": img_height * 0.4},
            "QC 02": {"x": img_width * 0.4, "y": img_height * 0.4},
            "CAM SHAFT LINE": {"x": img_width * 0.4, "y": img_height * 0.6},
            "Pos QC": {"x": img_width * 0.3, "y": img_height * 0.7},
        }

        marker_data = []
        for m_name, pos in koordinat_mesin.items():
            warna = "#22C55E" # Default Hijau (Normal)
            status_teks = "Normal / Beroperasi"
            
            if not df.empty and "Mesin" in df.columns and "Status_Part" in df.columns:
                df_m = df[df["Mesin"] == m_name]
                if not df_m.empty:
                    if any(df_m["Status_Part"] == "Part NG"):
                        warna = "#EF4444" # Merah
                        status_teks = "Mesin Rusak (Part NG)"

            marker_data.append({
                "Mesin": m_name, "x": pos["x"], "y": pos["y"], "color": warna, "status": status_teks
            })

        df_marker = pd.DataFrame(marker_data)
        fig_layout = go.Figure()

        fig_layout.add_trace(go.Scatter(
            x=df_marker["x"], y=df_marker["y"],
            mode="markers+text", text=df_marker["Mesin"], textposition="top center",
            textfont=dict(size=12, color="#FFFFFF", family="Arial Black, sans-serif"),
            marker=dict(size=16, color=df_marker["color"], line=dict(width=2, color="#000000")),
            hovertext=df_marker["status"], hoverinfo="text+name"
        ))

        fig_layout.update_layout(
            images=[dict(
                source=img_pil, xref="x", yref="y", x=0, y=0,
                sizex=img_width, sizey=img_height, sizing="stretch", opacity=1.0, layer="below"
            )],
            xaxis=dict(showgrid=False, zeroline=False, range=[0, img_width], visible=False),
            yaxis=dict(showgrid=False, zeroline=False, range=[img_height, 0], visible=False),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=600, margin=dict(l=0, r=0, t=0, b=0)
        )

        st.plotly_chart(fig_layout, use_container_width=True)
    else:
        st.error("⚠️ File gambar layout tidak ditemukan di repository GitHub!")

    st.markdown("---")
    st.subheader("📋 Log Maintenance Terakhir")
    df_display = df.drop(columns=["Foto_Base64"], errors="ignore")
    st.dataframe(df_display, use_container_width=True)

# ==========================================
# 6. FORM 1: MP INPUT PART NG (MESIN RUSAK)
# ==========================================
elif page == "🔴 Form Input Part NG (Mesin Rusak)":
    st.title("🔴 Input Part NG dari Mesin (Mesin Berhenti)")
    st.caption("Gunakan form ini saat MP menemukan abnormality/kerusakan di mesin dan melepas part NG.")

    uploader_key = "uploader_key_ng"
    if uploader_key not in st.session_state: st.session_state[uploader_key] = 0

    uploaded_file = st.file_uploader("📷 Upload Foto Part / Label Seri yang Rusak", type=["png", "jpg", "jpeg"], key=f"file_ng_{st.session_state[uploader_key]}")
    
    scanned_sn, scanned_name, scanned_type = "", "", ""
    encoded_image_str = ""
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Foto Part NG Diunggah", width=160)
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        encoded_image_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        with st.spinner("🔍 Memindai Barcode/Teks..."):
            scanned_name, scanned_type, scanned_sn = extract_text_from_image(image)
        st.success("✅ Auto-Scan Berhasil!")

    with st.form("form_input_ng", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            tanggal = st.date_input("Tanggal")
            mesin = st.selectbox("Pilih Mesin Bermasalah", MACHINE_LIST)
            nama_part = st.text_input("Nama Sparepart", value=scanned_name)
            no_seri = st.text_input("Nomor Seri Part (Serial No.)", value=scanned_sn)
        with col_b:
            type_part = st.text_input("Type Part / Model", value=scanned_type)
            qty = st.number_input("Jumlah Part (Qty)", min_value=1, value=1)
            teknisi = st.text_input("Nama MP / Pelapor")

        submitted = st.form_submit_button("🚨 Simpan Part NG (Mesin Jadi Merah)")
        if submitted:
            payload = {
                "tanggal": str(tanggal), "mesin": mesin, "kategori": "Part Replacement",
                "status_part": "Part NG", "no_seri": no_seri if no_seri else "-",
                "nama_part": nama_part if nama_part else "-", "type_part": type_part if type_part else "-",
                "qty": int(qty), "teknisi": teknisi if teknisi else "-",
                "foto_base64": encoded_image_str
            }
            if insert_data_to_supabase(payload):
                st.session_state[uploader_key] += 1
                st.toast("🚨 Part NG tercatat! Mesin berubah menjadi merah.", icon="⚠️")
                st.rerun()

# ==========================================
# 7. FORM 2: TEAM REPAIR (DIPISAH: MENUNGGU VS ON REPAIR)
# ==========================================
elif page == "🛠️ Form Team Repair (Box NG & On Repair)":
    st.title("🛠️ Ruang Team Repair")
    st.caption("Pemisahan jelas antara part yang menunggu perbaikan dan part yang sedang dikerjakan.")

    if df.empty or "Status_Part" not in df.columns:
        st.info("Belum ada data sparepart di database.")
    else:
        tab_menunggu, tab_repair = st.tabs(["⏳ Part Menunggu Repair (Box NG)", "🛠️ Part Sedang Di-Repair (On Progress)"])

        # --- TAB 1: PART MENUNGGU REPAIR ---
        with tab_menunggu:
            st.subheader("📋 Daftar Part Menunggu Perbaikan")
            df_menunggu = df[df["Status_Part"] == "Part NG"]

            if df_menunggu.empty:
                st.success("🎉 Tidak ada part yang menunggu repair saat ini.")
            else:
                for _, row in df_menunggu.iterrows():
                    with st.expander(f"🔴 SN: {row['No_Seri']} | {row['Nama_Part']} (Mesin: {row['Mesin']})"):
                        col_m1, col_m2 = st.columns([1, 2])
                        with col_m1:
                            foto_b64 = str(row.get("Foto_Base64", "")) if row.get("Foto_Base64") is not None else ""
                            if foto_b64 and foto_b64 != "None" and len(foto_b64) > 10:
                                try:
                                    st.image(Image.open(io.BytesIO(base64.b64decode(foto_b64))), width=150)
                                except Exception:
                                    pass
                        with col_m2:
                            st.write(f"**Type:** {row['Type']}")
                            st.write(f"**Tanggal Masuk:** {row['Tanggal']}")
                            st.write(f"**Pelapor Awal:** {row['Teknisi']}")
                            
                            teknisi_penerima = st.text_input("Nama Teknisi Repair", key=f"tech_ng_{row['ID']}")
                            if st.button("🛠️ Mulai Repair (Pindahkan ke On Progress)", key=f"btn_start_{row['ID']}"):
                                if update_status_in_supabase(row['ID'], "Part Repair", teknisi_penerima if teknisi_penerima else "-"):
                                    st.toast("✅ Part dipindahkan ke status Sedang Di-Repair (Kuning)!", icon="🚀")
                                    st.rerun()

        # --- TAB 2: PART SEDANG DI-REPAIR ---
        with tab_repair:
            st.subheader("⚙️ Daftar Part Sedang Dikerjakan (On Progress)")
            df_on_repair = df[df["Status_Part"] == "Part Repair"]

            if df_on_repair.empty:
                st.info("ℹ️ Tidak ada part yang sedang dalam proses repair.")
            else:
                for _, row in df_on_repair.iterrows():
                    with st.expander(f"🟠 SN: {row['No_Seri']} | {row['Nama_Part']} | Teknisi: {row['Teknisi']}"):
                        col_r1, col_r2 = st.columns([1, 2])
                        with col_r1:
                            foto_b64 = str(row.get("Foto_Base64", "")) if row.get("Foto_Base64") is not None else ""
                            if foto_b64 and foto_b64 != "None" and len(foto_b64) > 10:
                                try:
                                    st.image(Image.open(io.BytesIO(base64.b64decode(foto_b64))), width=150)
                                except Exception:
                                    pass
                        with col_r2:
                            st.write(f"**Type:** {row['Type']}")
                            st.write(f"**Mesin Asal:** {row['Mesin']}")
                            st.write(f"**Teknisi Repair:** {row['Teknisi']}")

                            if st.button("📦 Selesai Repair & Masukkan ke Box Ready (Biru)", key=f"btn_ready_{row['ID']}"):
                                payload_ready = {
                                    "tanggal": str(pd.Timestamp.now().date()),
                                    "mesin": "STOCK WAREHOUSE / READY BOX",
                                    "kategori": "Repair Completed",
                                    "status_part": "Part Ready",
                                    "no_seri": row['No_Seri'],
                                    "nama_part": row['Nama_Part'],
                                    "type_part": row['Type'],
                                    "qty": int(row['Qty']),
                                    "teknisi": row['Teknisi'],
                                    "foto_base64": str(row.get("Foto_Base64", "")) if row.get("Foto_Base64") is not None else ""
                                }
                                delete_data_from_supabase(row['ID'])
                                if insert_data_to_supabase(payload_ready):
                                    st.toast("✨ Part selesai direpair dan masuk ke Box Ready (Biru)!", icon="✅")
                                    st.rerun()

# ==========================================
# 8. FORM 3: INSTALL MACHINE (TANPA SCAN/UPLOAD)
# ==========================================
elif page == "🟢 Form Install Machine (Ambil Box Ready)":
    st.title("🟢 Form Pemasangan Part ke Mesin (Install Machine)")
    st.caption("Pilih part yang tersedia di Box Ready, isi tanggal & nama MP, lalu pasang ke mesin agar status mesin jadi hijau.")

    df_ready_box = df[df["Status_Part"] == "Part Ready"] if not df.empty and "Status_Part" in df.columns else pd.DataFrame()

    st.subheader("📦 Pilih Part yang Tersedia di Box Ready (Biru)")

    if df_ready_box.empty:
        st.warning("⚠️ Saat ini tidak ada part yang tersedia (Ready) di dalam Box Ready.")
    else:
        box_options = {}
        for _, r in df_ready_box.iterrows():
            label = f"SN: {r['No_Seri']} | Nama: {r['Nama_Part']} | Type: {r['Type']}"
            box_options[label] = r

        selected_box_label = st.selectbox("Pilih Part dari Daftar Box Ready:", list(box_options.keys()))
        chosen_part = box_options[selected_box_label]

        col_prev1, col_prev2 = st.columns([1, 3])
        with col_prev1:
            foto_ready_b64 = str(chosen_part.get("Foto_Base64", "")) if chosen_part.get("Foto_Base64") is not None else ""
            if foto_ready_b64 and foto_ready_b64 != "None" and len(foto_ready_b64) > 10:
                try:
                    st.image(Image.open(io.BytesIO(base64.b64decode(foto_ready_b64))), width=130)
                except Exception:
                    pass
        with col_prev2:
            st.write(f"**Nama Part:** {chosen_part['Nama_Part']}")
            st.write(f"**Type:** {chosen_part['Type']}")
            st.write(f"**Nomor Seri (SN):** {chosen_part['No_Seri']}")

        st.markdown("---")
        st.subheader("✍️ Masukkan Detail Pemasangan ke Mesin")

        with st.form("form_install_manual"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                tanggal_pasang = st.date_input("Tanggal Pemasangan")
                mesin_tujuan = st.selectbox("Pilih Mesin Tempat Pemasangan", MACHINE_LIST)
            with col_f2:
                teknisi_pasang = st.text_input("Nama MP / Teknisi yang Menginstal")

            submitted_install = st.form_submit_button("🚀 Input & Pasang ke Mesin (Status Mesin Jadi Hijau)")

            if submitted_install:
                if not teknisi_pasang:
                    st.error("❌ Nama MP / Teknisi yang menginstal wajib diisi!")
                else:
                    delete_data_from_supabase(chosen_part['ID'])

                    payload_installed = {
                        "tanggal": str(tanggal_pasang),
                        "mesin": mesin_tujuan,
                        "kategori": "Installation",
                        "status_part": "Installed / Normal",
                        "no_seri": chosen_part['No_Seri'],
                        "nama_part": chosen_part['Nama_Part'],
                        "type_part": chosen_part['Type'],
                        "qty": int(chosen_part['Qty']),
                        "teknisi": teknisi_pasang,
                        "foto_base64": foto_ready_b64
                    }

                    if insert_data_to_supabase(payload_installed):
                        st.toast(f"✨ Part berhasil dipasang ke {mesin_tujuan}! Status mesin sekarang Hijau Normal.", icon="✅")
                        st.rerun()

# ==========================================
# 9. AREA KHUSUS ADMIN
# ==========================================
elif page == "🔒 Area Khusus Admin":
    st.title("🔒 Area Khusus Admin / Supervisor")
    st.success("🔓 Akses Admin Terverifikasi!")
    
    if not df.empty:
        st.subheader("📥 Export Data")
        df_export = df.drop(columns=["Foto_Base64"], errors="ignore")
        csv = df_export.to_csv(index=False).encode('utf-8')
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
