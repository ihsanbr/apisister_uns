import streamlit as st
import pandas as pd
import json
import io
import time
import re
from sister_client import SisterAPIClient

st.set_page_config(
    page_title="Dashboard API SISTER - Kemdiktisaintek",
    page_icon="??",
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

def clean_dataframe_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Membersihkan karakter kontrol ASCII non-printable yang menyebabkan 
    openpyxl.utils.exceptions.IllegalCharacterError saat export ke Excel.
    """
    if df is None or df.empty:
        return df
    
    df_clean = df.copy()
    illegal_char_regex = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]')
    
    def sanitize_val(val):
        if isinstance(val, str):
            return illegal_char_regex.sub('', val)
        elif isinstance(val, (dict, list)):
            return illegal_char_regex.sub('', json.dumps(val, ensure_ascii=False))
        return val

    for col in df_clean.columns:
        df_clean[col] = df_clean[col].apply(sanitize_val)
        
    return df_clean

st.markdown('<div class="main-header">Dashboard Konektor API SISTER Kemdiktisaintek</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Aplikasi lengkap untuk Tarik Data (GET) & Push Data (POST) dari/ke API SISTER Kemdiktisaintek.</div>', unsafe_allow_html=True)

# Inisialisasi Session State
if "client" not in st.session_state:
    st.session_state.client = None
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "sdm_list" not in st.session_state:
    st.session_state.sdm_list = []

# Sidebar - Kredensial & Pengaturan
st.sidebar.header("Kredensial API SISTER")

env_choice = st.sidebar.radio(
    "Pilih Environment:",
    ["Production", "Sandbox (Uji Coba)"],
    index=0
)
is_sandbox = (env_choice == "Sandbox (Uji Coba)")

username = st.sidebar.text_input("Username API:", value="", type="default")
password = st.sidebar.text_input("Password API:", value="", type="password")
id_pengguna = st.sidebar.text_input("ID Pengguna (UUID):", value="")

connect_btn = st.sidebar.button("Hubungkan / Authorize", use_container_width=True)

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
                st.sidebar.success("Berhasil Autentikasi!")
                
                try:
                    sdm_data = client.get_sdm_list()
                    st.session_state.sdm_list = sdm_data
                    st.sidebar.info(f"Loaded {len(sdm_data)} data SDM.")
                except Exception as e:
                    st.sidebar.warning(f"Otentikasi berhasil, tapi gagal ambil daftar SDM: {e}")
            else:
                st.session_state.is_authenticated = False
                st.sidebar.error(f"Gagal Autentikasi: {res.get('error')}")

# Status Badge di Sidebar
if st.session_state.is_authenticated:
    st.sidebar.success("Status: Terhubung ke SISTER")
else:
    st.sidebar.warning("Status: Belum Terhubung")

# DAFTAR ENDPOINT LENGKAP SISTER API v1.0
ALL_GET_CATEGORIES = {
    "Data Pribadi / Profil": "/data_pribadi/profil",
    "Inpassing / Kesetaraan": "/inpassing",
    "Jabatan Fungsional": "/jabatan_fungsional",
    "Pangkat / Golongan": "/pangkat",
    "Sertifikasi Dosen": "/sertifikasi",
    "Tes / Ujian": "/tes",
    "Pendidikan Formal": "/pendidikan_formal",
    "Diklat / Pelatihan": "/diklat",
    "Bimbingan Mahasiswa": "/bimbingan_mahasiswa",
    "Pengajaran Dosen": "/pengajaran",
    "Bahan Ajar": "/bahan_ajar",
    "Tugas Tambahan": "/tugas_tambahan",
    "Penelitian": "/penelitian",
    "Publikasi Ilmiah": "/publikasi",
    "Paten / Kekayaan Intelektual": "/paten",
    "Pengabdian Masyarakat": "/pengabdian",
    "Pembicara / Orasi Ilmiah": "/pembicara",
    "Jabatan Pengelola Jurnal": "/pengelola_jurnal",
    "Anggota Organisasi Profesi": "/anggota_profesi",
    "Penghargaan / Tanda Jasa": "/penghargaan",
    "Kesejahteraan / Asuransi": "/kesejahteraan",
    "Dokumen SDM": "/dokumen"
}

ALL_PUSH_CATEGORIES = {
    "Push Pendidikan Formal": "/pendidikan_formal",
    "Push Diklat / Pelatihan": "/diklat",
    "Push Penelitian": "/penelitian",
    "Push Publikasi Ilmiah": "/publikasi",
    "Push Paten / Kekayaan Intelektual": "/paten",
    "Push Pengabdian Masyarakat": "/pengabdian",
    "Push Pembicara / Orasi": "/pembicara",
    "Push Bahan Ajar": "/bahan_ajar",
    "Push Anggota Profesi": "/anggota_profesi",
    "Push Penghargaan": "/penghargaan",
    "Push Dokumen SDM": "/dokumen"
}

# Tab Utama
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Status & Koneksi", 
    "Daftar SDM (Query Awal)", 
    "Tarik Data (GET)", 
    "Push Data ke SISTER (POST)",
    "Panduan"
])

# TAB 1: STATUS
with tab1:
    st.subheader("Informasi Koneksi API")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Environment:** {'Sandbox (Uji Coba)' if is_sandbox else 'Production'}")
        st.markdown(f"**Base URL:** `{SisterAPIClient(is_sandbox=is_sandbox).base_url}`")
        
    with col2:
        st.markdown(f"**Status Otentikasi:** {'Terautorisasi' if st.session_state.is_authenticated else 'Belum Terautorisasi'}")
        if st.session_state.is_authenticated and st.session_state.client and st.session_state.client.token:
            st.code(f"Token: {st.session_state.client.token[:20]}...{st.session_state.client.token[-10:]}", language="text")

    st.divider()
    st.subheader("Cek Kesehatan Koneksi")
    if st.button("Reload Daftar SDM"):
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

# TAB 2: DAFTAR SDM
with tab2:
    st.subheader("Daftar SDM / Dosen (Query Awal)")
    st.caption("Gunakan tabel ini untuk melihat seluruh SDM di PT Anda serta mendapatkan id_sdm UUID.")
    
    if not st.session_state.sdm_list:
        st.info("Belum ada data SDM. Hubungkan ke API SISTER di panel sebelah kiri untuk memuat data.")
    else:
        df_sdm = pd.DataFrame(st.session_state.sdm_list)
        
        search_query = st.text_input("Cari berdasarkan Nama, NIDN, NIP, atau ID:", "")
        if search_query:
            df_filtered = df_sdm[
                df_sdm.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
            ]
        else:
            df_filtered = df_sdm
            
        st.dataframe(df_filtered, use_container_width=True)
        st.caption(f"Menampilkan {len(df_filtered)} dari {len(df_sdm)} SDM.")
        
        df_sdm_export = clean_dataframe_for_excel(df_filtered)
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv_sdm = df_sdm_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Daftar SDM (.CSV)",
                data=csv_sdm,
                file_name="daftar_sdm_sister.csv",
                mime="text/csv"
            )
        with col_dl2:
            buffer_excel = io.BytesIO()
            with pd.ExcelWriter(buffer_excel, engine='openpyxl') as writer:
                df_sdm_export.to_excel(writer, index=False, sheet_name='Daftar SDM')
            st.download_button(
                label="Download Daftar SDM (.XLSX)",
                data=buffer_excel.getvalue(),
                file_name="daftar_sdm_sister.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# TAB 3: TARIK DATA (GET)
with tab3:
    st.subheader("Tarik & Download Data Detail dari SISTER (GET)")
    
    if not st.session_state.is_authenticated:
        st.warning("Anda perlu terhubung/authorize ke API SISTER terlebih dahulu.")
    else:
        col_cat, col_mode = st.columns(2)
        
        with col_cat:
            selected_cat_name = st.selectbox("Pilih Kategori Data SISTER:", list(ALL_GET_CATEGORIES.keys()))
            selected_endpoint = ALL_GET_CATEGORIES[selected_cat_name]
            
        with col_mode:
            download_mode = st.radio(
                "Pilih Cakupan Download:",
                ["Satu Dosen Spesifik", "Upload Excel List Dosen Target", "SEMUA Dosen (Batch Download)"],
                index=0,
                horizontal=False
            )

        target_id_sdm = None
        target_sdm_list = []
        
        if download_mode == "Satu Dosen Spesifik":
            if st.session_state.sdm_list:
                sdm_options = {}
                for item in st.session_state.sdm_list:
                    label = f"{item.get('nama', 'Tanpa Nama')} (NIDN: {item.get('nidn', '-')}) [{item.get('id_sdm')}]"
                    sdm_options[label] = item
                
                selected_sdm_label = st.selectbox("Pilih Dosen / SDM Target:", list(sdm_options.keys()))
                target_sdm_obj = sdm_options[selected_sdm_label]
                target_id_sdm = target_sdm_obj.get("id_sdm")
            else:
                target_id_sdm = st.text_input("Masukkan id_sdm manual (UUID):", "")
                
        elif download_mode == "Upload Excel List Dosen Target":
            st.info("Upload file Excel/CSV berisi NUPTK, NIDN, NIP, atau Nama Dosen target.")
            uploaded_file = st.file_uploader("Upload File Excel/CSV List Dosen:", type=["xlsx", "xls", "csv"], key="get_upload")
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df_upload = pd.read_csv(uploaded_file)
                    else:
                        df_upload = pd.read_excel(uploaded_file)
                    
                    st.write("Preview File yang Diupload:")
                    st.dataframe(df_upload.head(5), use_container_width=True)
                    
                    if st.session_state.sdm_list:
                        search_values = set()
                        for col in df_upload.columns:
                            vals = df_upload[col].dropna().astype(str).str.strip().tolist()
                            search_values.update(vals)
                        
                        matched_sdms = []
                        matched_ids = set()
                        
                        for sdm_item in st.session_state.sdm_list:
                            s_id = str(sdm_item.get("id_sdm", "")).strip()
                            s_nidn = str(sdm_item.get("nidn", "")).strip()
                            s_nip = str(sdm_item.get("nip", "")).strip()
                            s_nama = str(sdm_item.get("nama", "")).strip().lower()
                            s_nuptk = str(sdm_item.get("nuptk", "")).strip()
                            
                            is_match = False
                            for val in search_values:
                                val_clean = val.strip()
                                val_lower = val_clean.lower()
                                if val_clean and (
                                    val_clean == s_id or 
                                    val_clean == s_nidn or 
                                    val_clean == s_nip or 
                                    val_clean == s_nuptk or 
                                    (len(val_lower) > 3 and val_lower in s_nama)
                                ):
                                    is_match = True
                                    break
                            
                            if is_match and s_id not in matched_ids:
                                matched_ids.add(s_id)
                                matched_sdms.append(sdm_item)
                        
                        target_sdm_list = matched_sdms
                        
                        if target_sdm_list:
                            st.success(f"{len(target_sdm_list)} Dosen berhasil dicocokkan dengan SISTER!")
                            with st.expander("Lihat Dosen Terfilter:"):
                                st.dataframe(pd.DataFrame(target_sdm_list)[["nama", "nidn", "nip", "id_sdm"]], use_container_width=True)
                        else:
                            st.warning("Tidak ada Dosen yang cocok. Pastikan ada NIDN/NIP/NUPTK/Nama yang sesuai.")
                except Exception as e:
                    st.error(f"Gagal membaca file upload: {e}")
                    
        else:
            target_sdm_list = st.session_state.sdm_list
            total_sdm_count = len(target_sdm_list)
            st.info(f"Mode SEMUA Dosen akan menarik data {selected_cat_name} untuk {total_sdm_count} SDM/Dosen.")

        fetch_data_btn = st.button("Tarik Data dari API SISTER", type="primary")
        
        if fetch_data_btn:
            client = st.session_state.client
            
            if download_mode == "Satu Dosen Spesifik":
                if not target_id_sdm:
                    st.error("Silakan pilih Dosen terlebih dahulu.")
                else:
                    with st.spinner(f"Mengambil data {selected_cat_name}..."):
                        res_data = client.get_sdm_data(selected_endpoint, id_sdm=target_id_sdm)
                        
                        if isinstance(res_data, dict) and "error" in res_data:
                            st.error(f"Gagal mengambil data: {res_data.get('detail')}")
                        else:
                            st.success("Data berhasil ditarik!")
                            
                            if isinstance(res_data, list):
                                if len(res_data) > 0:
                                    df_res = pd.DataFrame(res_data)
                                    st.dataframe(df_res, use_container_width=True)
                                    df_res_clean = clean_dataframe_for_excel(df_res)
                                    
                                    buffer = io.BytesIO()
                                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                        df_res_clean.to_excel(writer, index=False, sheet_name='Data_SISTER')
                                    
                                    st.download_button(
                                        label="Download Data (.XLSX)",
                                        data=buffer.getvalue(),
                                        file_name=f"SISTER_{selected_cat_name.replace(' ', '_')}_{target_id_sdm[:8]}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                                else:
                                    st.info("Data kosong untuk SDM yang dipilih.")
                            else:
                                st.json(res_data)
                                json_bytes = json.dumps(res_data, indent=2).encode('utf-8')
                                st.download_button(
                                    label="Download JSON Data",
                                    data=json_bytes,
                                    file_name=f"SISTER_{selected_cat_name.replace(' ', '_')}.json",
                                    mime="application/json"
                                )
            else:
                if not target_sdm_list:
                    st.error("Daftar Dosen target kosong.")
                else:
                    st.write(f"Memulai Penarikan Data untuk {len(target_sdm_list)} Dosen...")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    all_combined_data = []
                    total_sdm = len(target_sdm_list)
                    
                    for idx, sdm in enumerate(target_sdm_list):
                        sdm_id = sdm.get("id_sdm")
                        sdm_nama = sdm.get("nama", "Tanpa Nama")
                        sdm_nidn = sdm.get("nidn", "-")
                        
                        status_text.text(f"Processing ({idx+1}/{total_sdm}): {sdm_nama} (NIDN: {sdm_nidn})...")
                        progress_bar.progress((idx + 1) / total_sdm)
                        
                        try:
                            res_data = client.get_sdm_data(selected_endpoint, id_sdm=sdm_id)
                            
                            if isinstance(res_data, list) and len(res_data) > 0:
                                for row in res_data:
                                    if isinstance(row, dict):
                                        record = {
                                            "nama_sdm": sdm_nama,
                                            "nidn": sdm_nidn,
                                            "id_sdm": sdm_id
                                        }
                                        record.update(row)
                                        all_combined_data.append(record)
                            elif isinstance(res_data, dict) and "error" not in res_data and len(res_data) > 0:
                                record = {
                                    "nama_sdm": sdm_nama,
                                    "nidn": sdm_nidn,
                                    "id_sdm": sdm_id
                                }
                                record.update(res_data)
                                all_combined_data.append(record)
                        except Exception as e:
                            st.warning(f"Gagal mengambil data untuk {sdm_nama}: {e}")
                        
                        time.sleep(0.1)
                    
                    status_text.text("Selesai memproses seluruh dosen target!")
                    
                    if all_combined_data:
                        df_all = pd.DataFrame(all_combined_data)
                        st.success(f"Selesai! Berhasil menarik {len(df_all)} baris data.")
                        st.dataframe(df_all, use_container_width=True)
                        
                        df_all_clean = clean_dataframe_for_excel(df_all)
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            buffer_all = io.BytesIO()
                            with pd.ExcelWriter(buffer_all, engine='openpyxl') as writer:
                                df_all_clean.to_excel(writer, index=False, sheet_name=selected_cat_name[:30])
                            
                            st.download_button(
                                label=f"Download Hasil - {selected_cat_name} (.XLSX)",
                                data=buffer_all.getvalue(),
                                file_name=f"SISTER_EXPORT_{selected_cat_name.replace(' ', '_')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
                        with col_d2:
                            csv_bytes = df_all_clean.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label=f"Download Hasil - {selected_cat_name} (.CSV)",
                                data=csv_bytes,
                                file_name=f"SISTER_EXPORT_{selected_cat_name.replace(' ', '_')}.csv",
                                mime="text/csv"
                            )
                    else:
                        st.info(f"Tidak ada data ditemukan untuk kategori {selected_cat_name} pada dosen target.")

# TAB 4: PUSH DATA (POST)
with tab4:
    st.subheader("Push / Masukkan Data Baru ke SISTER (POST Request)")
    st.caption("Gunakan menu ini untuk memasukkan data luar (misal: Penelitian, Publikasi, Dokumen) ke dalam sistem SISTER menggunakan file Excel.")
    
    if not st.session_state.is_authenticated:
        st.warning("Anda perlu terhubung/authorize ke API SISTER terlebih dahulu.")
    else:
        col_push_cat, col_push_info = st.columns(2)
        
        with col_push_cat:
            selected_push_name = st.selectbox("Pilih Kategori Endpoint Push Data:", list(ALL_PUSH_CATEGORIES.keys()))
            selected_push_endpoint = ALL_PUSH_CATEGORIES[selected_push_name]
            
        with col_push_info:
            st.info(f"Target Endpoint: POST {selected_push_endpoint}")
            st.caption("Pastikan file Excel memiliki nama kolom (header) yang persis sama dengan nama field atribut JSON SISTER.")

        push_file = st.file_uploader("Upload Excel / CSV Berisi Data yang Akan Dipush:", type=["xlsx", "xls", "csv"], key="push_upload")
        
        if push_file is not None:
            try:
                if push_file.name.endswith('.csv'):
                    df_push = pd.read_csv(push_file)
                else:
                    df_push = pd.read_excel(push_file)
                
                st.write("Preview Data yang Akan Dikirim ke SISTER:")
                st.dataframe(df_push, use_container_width=True)
                
                total_rows = len(df_push)
                st.warning(f"Anda akan mengirim {total_rows} baris data ke endpoint {selected_push_endpoint} di API SISTER.")
                
                confirm_push = st.checkbox("Saya yakin ingin mengirimkan data ini ke API SISTER.")
                
                if st.button("Mulai Push Data ke SISTER", type="primary", disabled=not confirm_push):
                    client = st.session_state.client
                    st.write("Memproses Pengiriman Data...")
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    results_log = []
                    success_cnt = 0
                    fail_cnt = 0
                    
                    records = df_push.to_dict(orient="records")
                    
                    for idx, row in enumerate(records):
                        payload = {k: v for k, v in row.items() if pd.notna(v)}
                        
                        status_text.text(f"Mengirim baris ({idx+1}/{total_rows})...")
                        progress_bar.progress((idx + 1) / total_rows)
                        
                        res = client.post_sdm_data(selected_push_endpoint, payload)
                        
                        if res["success"]:
                            success_cnt += 1
                            results_log.append({
                                "Baris": idx + 1,
                                "Status": "BERHASIL",
                                "HTTP Code": res["status_code"],
                                "Response": str(res["response"])[:150]
                            })
                        else:
                            fail_cnt += 1
                            results_log.append({
                                "Baris": idx + 1,
                                "Status": "GAGAL",
                                "HTTP Code": res["status_code"],
                                "Response": str(res["response"])[:150]
                            })
                        
                        time.sleep(0.2)
                    
                    status_text.text("Proses Push Data Selesai!")
                    
                    col_p1, col_p2 = st.columns(2)
                    col_p1.metric("Berhasil Dipush", f"{success_cnt} Rows")
                    col_p2.metric("Gagal Dipush", f"{fail_cnt} Rows")
                    
                    df_log = pd.DataFrame(results_log)
                    st.write("Log Hasil Pengiriman Data:")
                    st.dataframe(df_log, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Gagal memproses file push data: {e}")

# TAB 5: PANDUAN
with tab5:
    st.subheader("Cara Menggunakan Dashboard API SISTER")
    st.markdown("""
    ### 1. Otentikasi (Authorize)
    * Masukkan **Username**, **Password**, dan **ID Pengguna (UUID)** yang didapatkan dari portal SISTER WS.
    * Klik **Hubungkan / Authorize**. Dashboard akan menyimpan Bearer Token secara otomatis.

    ---

    ### 2. Tarik Data (GET Request)
    * **Satu Dosen Spesifik:** Memilih 1 dosen dari dropdown untuk diunduh riwayatnya.
    * **Upload Excel List Dosen Target:** Memasukkan Excel/CSV berisi daftar NUPTK/NIDN/NIP/Nama target.
    * **SEMUA Dosen:** Menarik data secara otomatis untuk seluruh SDM di Perguruan Tinggi.

    ---

    ### 3. Push Data (POST Request)
    * Digunakan untuk memasukkan data dari aplikasi luar (misal: SIMLitabmas lokal, Sistem Repository, SIAKAD) langsung ke dalam database SISTER.
    * Buat file Excel dengan nama kolom yang **persis sama** dengan nama atribut JSON di SISTER (misal: `id_sdm`, `judul`, `tahun_pelaksanaan`, dll).
    * Unggah file, lakukan pratinjau, lalu klik **Mulai Push Data**.
    """)