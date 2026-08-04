import streamlit as st
import pandas as pd
from PIL import Image
import io, base64
from supabase import create_client

st.set_page_config(page_title="Team Repair", page_icon="🛠️", layout="wide")
st.markdown("""<style>.stApp { background: linear-gradient(135deg, #0B0F19 0%, #111827 50%, #0F172A 100%); color: #F3F4F6; }</style>""", unsafe_allow_html=True)

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
        return pd.DataFrame(res.data) if res.data else pd.DataFrame()
    except: return pd.DataFrame()

df = load_data()

st.title("🛠️ Ruang Team Repair")
st.caption("Halaman khusus manajemen perbaikan sparepart.")
st.markdown("---")

if not df.empty and "status_part" in df.columns:
    df_ng = df[df["status_part"] == "Part NG"]
    st.subheader(f"Daftar Part Menunggu Repair ({len(df_ng)})")
    for _, row in df_ng.iterrows():
        with st.expander(f"SN: {row.get('no_seri')} - {row.get('nama_part')}"):
            tech = st.text_input("Nama Teknisi", key=f"t_{row['id']}")
            if st.button("Mulai Repair", key=f"b_{row['id']}"):
                supabase.table("maintenance_log").update({"status_part": "Part Repair", "teknisi": tech}).eq("id", row['id']).execute()
                st.success("Dipindah ke On Progress!")
                st.rerun()
else:
    st.info("Tidak ada data antrean repair.")
