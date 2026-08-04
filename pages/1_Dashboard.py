import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
from supabase import create_client

st.set_page_config(page_title="Dashboard Maintenance", page_icon="📊", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0B0F19 0%, #111827 50%, #0F172A 100%); color: #F3F4F6; }
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        border-radius: 12px !important; padding: 8px !important; text-align: center;
    }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 800 !important; color: #38BDF8 !important; }
    @media (max-width: 768px) {
        .row-widget.stHorizontal { flex-direction: row !important; }
        [data-testid="column"] { flex: 1 !important; min-width: unset !important; }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_supabase():
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_KEY", "")
    if not url or not key: return None
    return create_client(url, key)

supabase = init_supabase()

def load_data():
    if supabase is None: return pd.DataFrame()
    try:
        res = supabase.table("maintenance_log").select("*").order("id", desc=True).execute()
        if res.data:
            df_res = pd.DataFrame(res.data)
            col_map = {"id": "ID", "tanggal": "Tanggal", "mesin": "Mesin", "status_part": "Status_Part", "nama_part": "Nama_Part", "type_part": "Type", "qty": "Qty", "teknisi": "Teknisi", "foto_base64": "Foto_Base64"}
            return df_res.rename(columns={k: v for k, v in col_map.items() if k in df_res.columns})
        return pd.DataFrame()
    except: return pd.DataFrame()

df = load_data()

st.title("🛡️ Executive Maintenance Dashboard")
st.caption("URL halaman ini unik dan dapat disalin dari browser untuk dibuatkan QR Code.")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
total_repair = len(df[df["Status_Part"] == "Part Repair"]) if not df.empty and "Status_Part" in df.columns else 0
total_ready = len(df[df["Status_Part"] == "Part Ready"]) if not df.empty and "Status_Part" in df.columns else 0
part_ng = len(df[df["Status_Part"] == "Part NG"]) if not df.empty and "Status_Part" in df.columns else 0

col1.metric("🛠️ On Repair", f"{total_repair}")
col2.metric("📦 Box Ready", f"{total_ready}")
col3.metric("⚠️ Mesin NG", f"{part_ng}")
col4.metric("📈 OEE", "84.2%")

st.markdown("---")
st.subheader("📋 Log Maintenance Terakhir")
if not df.empty:
    st.dataframe(df.drop(columns=["Foto_Base64"], errors="ignore"), use_container_width=True)
else:
    st.info("Belum ada data.")
