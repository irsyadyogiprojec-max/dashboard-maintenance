import streamlit as st
import pandas as pd
from PIL import Image
import io, base64, re, numpy as np
from supabase import create_client

try:
    import easyocr
    @st.cache_resource
    def load_ocr(): return easyocr.Reader(['en'], gpu=False)
    reader = load_ocr()
    HAS_OCR = True
except: HAS_OCR = False

st.set_page_config(page_title="Input Part NG", page_icon="🔴", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0B0F19 0%, #111827 50%, #0F172A 100%); color: #F3F4F6; }
    [data-testid="stForm"] { background: rgba(30, 41, 59, 0.4) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; border-radius: 16px !important; padding: 16px !important; }
    .stButton>button, div[data-testid="stFormSubmitButton"]>button { background: linear-gradient(90deg, #2563EB 0%, #7C3AED 100%) !important; color: #FFFFFF !important; border-radius: 10px !important; width: 100% !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if not url or not key: return None
    return create_client(url, key)

supabase = init_supabase()
MACHINE_LIST = ["CRANK SHAFT LINE", "QC 01", "ISP-017", "QC 02", "CYLINDER HEAD LINE", "CAM SHAFT LINE", "CYLINDER BLOCK LINE", "Pos QC"]

st.title("🔴 Form Input Part NG")
st.caption("Salin URL halaman ini untuk dijadikan QR Code khusus area mesin input NG.")
st.markdown("---")

uploaded_file = st.file_uploader("📷 Upload Foto Part Rusak", type=["png", "jpg", "jpeg"])
encoded_img = ""
if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, width=150)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    encoded_img = base64.b64encode(buf.getvalue()).decode("utf-8")

with st.form("form_ng", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        tgl = st.date_input("Tanggal")
        mesin = st.selectbox("Mesin", MACHINE_LIST)
        nama = st.text_input("Nama Sparepart")
        sn = st.text_input("Nomor Seri (SN)")
    with col2:
        tp = st.text_input("Type Part")
        qty = st.number_input("Qty", min_value=1, value=1)
        teknisi = st.text_input("Nama Pelapor")
    
    if st.form_submit_button("🚨 Simpan Part NG"):
        if supabase:
            payload = {"tanggal": str(tgl), "mesin": mesin, "kategori": "Part Replacement", "status_part": "Part NG", "no_seri": sn if sn else "-", "nama_part": nama if nama else "-", "type_part": tp if tp else "-", "qty": int(qty), "teknisi": teknisi if teknisi else "-", "foto_base64": encoded_img}
            supabase.table("maintenance_log").insert(payload).execute()
            st.success("Berhasil disimpan!")
            st.rerun()
