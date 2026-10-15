import streamlit as st
import pandas as pd
import json
import io
from sister_client import SisterAPIClient

st.set_page_config(
    page_title="Dashboard API SISTER - Kemdiktisaintek",
    page_icon="🎓",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 14px;
        color: #4B5563;
        margin-bottom: 25px;
    }
    .status-card {
        padding: 15px;
        border-radius: 8px;
        background-color: #F3F4F6;
        border-left: 5px solid #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎓 Dashboard Konektor API SISTER Kemdiktisaintek</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Aplikasi lokal untuk melakukan autentikasi, penjelajahan data SDM, dan penarikan data ke format Excel/CSV.</div>', unsafe_allow_html=True)

# Inisialisasi Session State
if "client" not in st.session_state:
    st.session_state.client = None
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "sdm_list" not in st.session_state:
    st.session_state.sdm_list = []

# Sidebar - Kredensial & Pengaturan
st.sidebar.header("🔑 Kredensial API SISTER")

env_choice = st.sidebar.radio(
    "Pilih Environment:",
    ["Production", "Sandbox (Uji Coba)"],
    index=0
)
is_sandbox = (env_choice == "Sandbox (Uji Coba)")

username = st.sidebar.text_input("Username API:", value="", type="default")
password = st.sidebar.text_input("Password API:", value="", type="password")
id_pengguna = st.sidebar.text_input("ID Pengguna (UUID):", value="")

connect_btn = st.sidebar.button("🔌 Hubungkan / Authorize", use_container_width=True)

if connect_btn:
    if not username or not password or not id_pengguna:
        st.sidebar.error("Mohon lengkapi Username, Password, dan ID Pengguna!")
    else:
        with st.spinner("Menghubungkan ke API SISTER..."):
            client = SisterAPIClient(is_sandbox=is_sandbox)
            res = client.authorize(username, password, id_pengguna)
            if res["success"]:
                st.session_state.client = client
                st.session_state.is_authenticated = True
                st.sidebar.success("✅ Berhasil Autentikasi!")
                
                # Otomatis ambil data SDM awal
                try:
                    sdm_data = client.get_sdm_list()
                    st.session_state.sdm_list = sdm_data
                    st.sidebar.info(f"Loaded {len(sdm_data)} data SDM.")
                except Exception as e:
                    st.sidebar.warning(f"Otentikasi berhasil, tapi gagal ambil daftar SDM: {e}")
            else:
                st.session_state.is_authenticated = False
                st.sidebar.error(f"❌ Gagal Autentikasi: {res.get('error')}")

# Status Badge di Sidebar
if st.session_state.is_authenticated:
    st.sidebar.success("🟢 Terhubung ke SISTER")
else:
    st.sidebar.warning("🔴 Belum Terhubung")

# Tab Layanan
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Status & Koneksi", 
    "👥 Daftar SDM (Query Awal)", 
    "📥 Tarik & Download Data", 
    "📖 Panduan Penggunaan"
])

with tab1:
    st.subheader("Informasi Koneksi")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Environment Active:** {'Sandbox' if is_sandbox else 'Production'}")
        st.markdown(f"**Base URL:** `{SisterAPIClient(is_sandbox=is_sandbox).base_url}`")
        
    with col2:
        st.markdown(f"**Status Otentikasi:** {'✅ Terautorisasi' if st.session_state.is_authenticated else '❌ Belum Terautorisasi'}")
        if st.session_state.is_authenticated and st.session_state.client.token:
            st.code(f"Token: {st.session_state.client.token[:20]}...{st.session_state.client.token[-10:]}", language="text")

    st.divider()
    st.subheader("Cek Kesehatan Koneksi API")
    if st.button("🔄 Reload Daftar SDM"):
        if not st.session_state.is_authenticated:
            st.error("Silakan lakukan authorization di sidebar terlebih dahulu.")
        else:
            with st.spinner("Mengambil daftar SDM..."):
                try:
                    data = st.session_state.client.get_sdm_list()
                    st.session_state.sdm_list = data
                    st.success(f"Berhasil memperbarui daftar SDM ({len(data)} Dosen/Pegawai ditemukan).")
                except Exception as e:
                    st.error(f"Gagal mengambil data: {e}")

with tab2:
    st.subheader("Daftar Sumber Daya Manusia (SDM) / Dosen")
    st.caption("Hasil endpoint `/referensi/sdm`. Gunakan tabel di bawah untuk menemukan `id_sdm` Dosen.")
    
    if not st.session_state.sdm_list:
        st.info("Belum ada data SDM. Hubungkan ke API SISTER di panel sebelah kiri untuk memuat data.")
    else:
        df_sdm = pd.DataFrame(st.session_state.sdm_list)
        
        # Search filter
        search_query = st.text_input("🔍 Cari berdasarkan Nama, NIDN, atau NIP:", "")
        if search_query:
            df_filtered = df_sdm[
                df_sdm.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
            ]
        else:
            df_filtered = df_sdm
            
        st.dataframe(df_filtered, use_container_width=True)
        st.caption(f"Menampilkan {len(df_filtered)} dari {len(df_sdm)} data.")
        
        # Download Button untuk list SDM
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv_sdm = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Daftar SDM (.CSV)",
                data=csv_sdm,
                file_name="daftar_sdm_sister.csv",
                mime="text/csv"
            )
        with col_dl2:
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, index=False, sheet_name='Daftar SDM')
            st.download_button(
                label="📊 Download Daftar SDM (.XLSX)",
                data=buffer_excel.getvalue(),
                file_name="daftar_sdm_sister.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

with tab3:
    st.subheader("Download Data Detail Spesifik SISTER")
    
    if not st.session_state.is_authenticated:
        st.warning("⚠️ Anda perlu terhubung/authorize ke API SISTER terlebih dahulu.")
    else:
        # Pilihan Endpoint Category
        categories = {
            "Data Pribadi / Profil": "/data_pribadi/profil",
            "Pendidikan Formal": "/pendidikan_formal",
            "Penelitian": "/penelitian",
            "Pengajaran": "/pengajaran",
            "Pengabdian": "/pengabdian",
            "Kualifikasi / Jabatan Akademik": "/kualifikasi",
            "Dokumen SDM": "/dokumen"
        }
        
        col_cat, col_sdm = st.columns(2)
        
        with col_cat:
            selected_cat_name = st.selectbox("Pilih Kategori Data:", list(categories.keys()))
            selected_endpoint = categories[selected_cat_name]
            
        with col_sdm:
            if st.session_state.sdm_list:
                sdm_options = {"-- Pilih SDM (Semua/Spesifik) --": None}
                for item in st.session_state.sdm_list:
                    label = f"{item.get('nama', 'Tanpa Nama')} (NIDN: {item.get('nidn', '-')}) [{item.get('id_sdm')}]"
                    sdm_options[label] = item.get("id_sdm")
                
                selected_sdm_label = st.selectbox("Pilih Dosen / SDM:", list(sdm_options.keys()))
                target_id_sdm = sdm_options[selected_sdm_label]
            else:
                target_id_sdm = st.text_input("Atau Masukkan `id_sdm` manual (UUID):", "")

        fetch_data_btn = st.button("🚀 Tarik Data dari API SISTER", type="primary")
        
        if fetch_data_btn:
            with st.spinner(f"Mengambil data {selected_cat_name}..."):
                client = st.session_state.client
                res_data = client.get_sdm_data(selected_endpoint, id_sdm=target_id_sdm)
                
                if isinstance(res_data, dict) and "error" in res_data:
                    st.error(f"Gagal mengambil data: {res_data.get('detail')}")
                else:
                    st.success("✅ Data berhasil ditarik!")
                    
                    # Tampilkan Preview JSON / DataFrame
                    if isinstance(res_data, list):
                        if len(res_data) > 0:
                            df_res = pd.DataFrame(res_data)
                            st.dataframe(df_res, use_container_width=True)
                            
                            # Excel Download
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                df_res.to_excel(writer, index=False, sheet_name='Data_SISTER')
                            
                            st.download_button(
                                label="📥 Download Data Detail (.XLSX)",
                                data=buffer.getvalue(),
                                file_name=f"SISTER_{selected_cat_name.replace(' ', '_')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.info("Data kosong untuk filter SDM yang dipilih.")
                    else:
                        st.json(res_data)
                        json_bytes = json.dumps(res_data, indent=2).encode('utf-8')
                        st.download_button(
                            label="📥 Download JSON Data",
                            data=json_bytes,
                            file_name=f"SISTER_{selected_cat_name.replace(' ', '_')}.json",
                            mime="application/json"
                        )

with tab4:
    st.subheader("📖 Cara Menggunakan Dashboard SISTER")
    st.markdown("""
    1. **Persiapan Kredensial API:**
       - Pastikan Admin PT Anda telah memberikan akses **SISTER WS Basic** atau **WS Pro**.
       - Salin `Username`, `Password`, dan `ID Pengguna` (UUID) dari menu **Kredensial API** di web SISTER.
    2. **Melakukan Authorize:**
       - Masukkan Kredensial pada sidebar sebelah kiri.
       - Klik tombol **Hubungkan / Authorize**.
       - Jika sukses, token akan disimpan otomatis selama sesi berlangsung (masa aktif 60 menit).
    3. **Query Awal (Daftar SDM):**
       - Buka tab **Daftar SDM** untuk melihat semua dosen/tenaga kependidikan yang terdaftar di PT Anda.
       - Cari nama atau NIDN dosen yang ingin dicari data riwayatnya.
    4. **Mengunduh Data:**
       - Buka tab **Tarik & Download Data**.
       - Pilih kategori data yang diinginkan (misal: Penelitian, Pendidikan Formal, Profil).
       - Pilih Dosen target atau kosongkan untuk semua SDM jika diizinkan endpoint.
       - Klik **Tarik Data**, kemudian klik tombol **Download (.XLSX)** atau **(.JSON)**.
    """)
