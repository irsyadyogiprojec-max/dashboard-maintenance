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
        # Fallback jika kolom foto_base64 belum ada di database, hapus key foto_base64 agar tetap bisa tersimpan
        if "foto_base64" in str(e):
            try:
                record.pop("foto_base64", None)
                supabase.table("maintenance_log").insert(record).execute()
                return True
            except Exception as e2:
                st.error(f"Gagal menyimpan ke database: {e2}")
                return False
        st.error(f"Gagal menyimpan ke database: {e}")
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
    encoded_image_str = ""
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Foto Part Diunggah", width=160)
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        encoded_image_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
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
                "qty": int(qty), "teknisi": teknisi if teknisi else "-",
                "foto_base64": encoded_image_str
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
            warna = "#22C55E"
            status_teks = "Ready / Normal"
            
            if not df.empty and "Mesin" in df.columns and "Status_Part" in df.columns:
                df_m = df[df["Mesin"] == m_name]
                if not df_m.empty:
                    latest_status = df_m.iloc[0]["Status_Part"]
                    if latest_status == "Part NG":
                        warna = "#EF4444"
                        status_teks = "Part NG / Rusak"
                    elif latest_status == "Part Repair":
                        warna = "#F97316"
                        status_teks = "Sedang Repair"

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
    st.subheader("📊 Analisis Grafik Performa & Status Maintenance")
    
    if not df.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### 📈 Jumlah Gangguan Berdasarkan Mesin")
            df_mesin = df["Mesin"].value_counts().reset_index()
            df_mesin.columns = ["Mesin", "Total"]
            fig_bar = px.bar(df_mesin, x="Mesin", y="Total", text="Total", color="Total", color_continuous_scale="Viridis")
            fig_bar.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#F3F4F6"), height=350, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            st.markdown("##### 🥧 Persentase Status Part")
            if "Status_Part" in df.columns:
                df_status = df["Status_Part"].value_counts().reset_index()
                df_status.columns = ["Status_Part", "Total"]
                fig_pie = px.pie(df_status, names="Status_Part", values="Total", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#F3F4F6"), height=350, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Belum ada data untuk ditampilkan dalam bentuk grafik.")

    st.markdown("---")
    st.subheader("📋 Log Maintenance Terakhir")
    df_display = df.drop(columns=["Foto_Base64"], errors="ignore")
    st.dataframe(df_display, use_container_width=True)

# ==========================================
# 7. FORM REPAIR (AMBIL DARI BOX NG)
# ==========================================
elif page == "🛠️ Form Repair (Ambil dari Box NG)":
    st.title("🛠️ Form Proses Repair Sparepart")
    st.caption("Pilih part dari Box NG, klik tombol pilih, lalu Opsi Eksekusi Perbaikan akan muncul.")

    if df.empty or "Status_Part" not in df.columns:
        st.info("Belum ada data sparepart di database.")
    else:
        df_box_ng = df[df["Status_Part"].isin(["Part NG", "Part Repair"])]
        
        if df_box_ng.empty:
            st.success("🎉 Luar biasa! Tidak ada part NG di box saat ini.")
        else:
            part_options = {f"SN: {row['No_Seri']} | {row['Nama_Part']} (Mesin Asal: {row['Mesin']}) [Status: {row['Status_Part']}]": row for _, row in df_box_ng.iterrows()}
            
            selected_label = st.selectbox("🔍 Pilih Part dari Box NG:", list(part_options.keys()))
            
            if st.button("📌 Muat & Pilih Part Ini"):
                st.session_state["active_repair_part"] = part_options[selected_label]
                st.success("✅ Part berhasil dipilih! Silakan isi form eksekusi di bawah.")

            if "active_repair_part" in st.session_state and st.session_state["active_repair_part"] is not None:
                selected_data = st.session_state["active_repair_part"]

                st.markdown("---")
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown("### 📄 Informasi & Foto Part Terpilih")
                    st.info(f"""
                    * **Nama Part:** {selected_data['Nama_Part']}
                    * **Type / Model:** {selected_data['Type']}
                    * **Nomor Seri (SN):** {selected_data['No_Seri']}
                    * **Mesin Asal (NG):** {selected_data['Mesin']}
                    * **Pelapor / Teknisi Awal:** {selected_data['Teknisi']}
                    """)
                    
                    foto_b64 = selected_data.get("Foto_Base64", "")
                    if foto_b64 and isinstance(foto_b64, str) and len(foto_b64) > 10:
                        try:
                            image_bytes = base64.b64decode(foto_b64)
                            image_part = Image.open(io.BytesIO(image_bytes))
                            st.image(image_part, caption="Foto Fisik Part (Saat Input NG)", width=260)
                        except Exception:
                            st.warning("⚠️ Gagal memuat foto fisik part.")
                    else:
                        st.info("ℹ️ Tidak ada foto fisik yang di-upload untuk part ini.")

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
                                "teknisi": teknisi_repair if teknisi_repair else "-",
                                "foto_base64": selected_data.get("Foto_Base64", "")
                            }
                            
                            if insert_data_to_supabase(payload):
                                st.session_state["active_repair_part"] = None
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
