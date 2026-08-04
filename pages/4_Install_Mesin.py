import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(page_title="Install Mesin", page_icon="🟢", layout="wide")
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
MACHINE_LIST = ["CRANK SHAFT LINE", "QC 01", "ISP-017", "QC 02", "CYLINDER HEAD LINE", "CAM SHAFT LINE", "CYLINDER BLOCK LINE", "Pos QC"]

st.title("🟢 Install Part ke Mesin")
st.caption("Pasang kembali sparepart dari Box Ready ke mesin produksi.")
st.markdown("---")

if not df.empty and "status_part" in df.columns:
    df_ready = df[df["status_part"] == "Part Ready"]
    if not df_ready.empty:
        options = {f"SN: {r['no_seri']} | {r['nama_part']}": r for _, r in df_ready.iterrows()}
        selected = st.selectbox("Pilih Part Ready", list(options.keys()))
        chosen = options[selected]
        
        with st.form("install_form"):
            tgl = st.date_input("Tanggal Pasang")
            mesin_tujuan = st.selectbox("Mesin Tujuan", MACHINE_LIST)
            teknisi = st.text_input("Teknisi yang Memasang")
            
            if st.form_submit_button("🚀 Pasang ke Mesin"):
                supabase.table("maintenance_log").delete().eq("id", chosen['id']).execute()
                payload = {"tanggal": str(tgl), "mesin": mesin_tujuan, "kategori": "Installation", "status_part": "Installed / Normal", "no_seri": chosen['no_seri'], "nama_part": chosen['nama_part'], "type_part": chosen['type_part'], "qty": chosen['qty'], "teknisi": teknisi, "foto_base64": chosen.get('foto_base64', '')}
                supabase.table("maintenance_log").insert(payload).execute()
                st.success("Berhasil dipasang ke mesin!")
                st.rerun()
    else:
        st.warning("Box Ready kosong.")
else:
    st.info("Belum ada data.")
