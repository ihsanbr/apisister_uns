import streamlit as st
import pandas as pd
import json
import io
import time
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
st.markdown('<div class="sub-header">Aplikasi lokal & cloud untuk otentikasi, penjelajahan data SDM, dan penarikan massal data SISTER ke format Excel/CSV.</div>', unsafe_allow_html=True)

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
        if st.session_state.is_authenticated and st.session_state.client and st.session_state.client.token:
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
        categories = {
            "Dokumen SDM": "/dokumen",
            "Data Pribadi / Profil": "/data_pribadi/profil",
            "Pendidikan Formal": "/pendidikan_formal",
            "Penelitian": "/penelitian",
            "Pengajaran": "/pengajaran",
            "Pengabdian": "/pengabdian",
            "Kualifikasi / Jabatan Akademik": "/kualifikasi"
        }
        
        col_cat, col_mode = st.columns(2)
        
        with col_cat:
            selected_cat_name = st.selectbox("Pilih Kategori Data:", list(categories.keys()))
            selected_endpoint = categories[selected_cat_name]
            
        with col_mode:
            download_mode = st.radio(
                "Pilih Cakupan Download:",
                ["Satu Dosen Spesifik", "🌐 SEMUA Dosen (Batch Download)"],
                index=0,
                horizontal=True
            )

        target_id_sdm = None
        selected_sdm_name = ""
        
        if download_mode == "Satu Dosen Spesifik":
            if st.session_state.sdm_list:
                sdm_options = {}
                for item in st.session_state.sdm_list:
                    label = f"{item.get('nama', 'Tanpa Nama')} (NIDN: {item.get('nidn', '-')}) [{item.get('id_sdm')}]"
                    sdm_options[label] = item
                
                selected_sdm_label = st.selectbox("Pilih Dosen / SDM Target:", list(sdm_options.keys()))
                target_sdm_obj = sdm_options[selected_sdm_label]
                target_id_sdm = target_sdm_obj.get("id_sdm")
                selected_sdm_name = target_sdm_obj.get("nama", "Tanpa Nama")
            else:
                target_id_sdm = st.text_input("Masukkan `id_sdm` manual (UUID):", "")
        else:
            total_sdm_count = len(st.session_state.sdm_list)
            st.info(f"ℹ️ Mode **SEMUA Dosen** akan menarik data kategori `{selected_cat_name}` secara otomatis untuk **{total_sdm_count} SDM/Dosen** yang terdaftar di PT Anda.")

        fetch_data_btn = st.button("🚀 Tarik Data dari API SISTER", type="primary")
        
        if fetch_data_btn:
            client = st.session_state.client
            
            # --- MODE 1: SATU DOSEN SPESIFIK ---
            if download_mode == "Satu Dosen Spesifik":
                with st.spinner(f"Mengambil data {selected_cat_name}..."):
                    res_data = client.get_sdm_data(selected_endpoint, id_sdm=target_id_sdm)
                    
                    if isinstance(res_data, dict) and "error" in res_data:
                        st.error(f"Gagal mengambil data: {res_data.get('detail')}")
                    else:
                        st.success("✅ Data berhasil ditarik!")
                        
                        if isinstance(res_data, list):
                            if len(res_data) > 0:
                                df_res = pd.DataFrame(res_data)
                                st.dataframe(df_res, use_container_width=True)
                                
                                buffer = io.BytesIO()
                                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                    df_res.to_excel(writer, index=False, sheet_name='Data_SISTER')
                                
                                st.download_button(
                                    label="📥 Download Data (.XLSX)",
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
                                label="📥 Download JSON Data",
                                data=json_bytes,
                                file_name=f"SISTER_{selected_cat_name.replace(' ', '_')}.json",
                                mime="application/json"
                            )

            # --- MODE 2: BATCH DOWNLOAD SEMUA DOSEN ---
            else:
                if not st.session_state.sdm_list:
                    st.error("Daftar SDM kosong. Silakan muat ulang daftar SDM terlebih dahulu.")
                else:
                    st.write("⏳ **Memulai Penarikan Data Massal... Mohon Jangan Tutup Halaman Ini.**")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    all_combined_data = []
                    total_sdm = len(st.session_state.sdm_list)
                    success_count = 0
                    
                    for idx, sdm in enumerate(st.session_state.sdm_list):
                        sdm_id = sdm.get("id_sdm")
                        sdm_nama = sdm.get("nama", "Tanpa Nama")
                        sdm_nidn = sdm.get("nidn", "-")
                        
                        status_text.text(f"Processing ({idx+1}/{total_sdm}): {sdm_nama} (NIDN: {sdm_nidn})...")
                        progress_bar.progress((idx + 1) / total_sdm)
                        
                        try:
                            res_data = client.get_sdm_data(selected_endpoint, id_sdm=sdm_id)
                            
                            if isinstance(res_data, list) and len(res_data) > 0:
                                success_count += 1
                                for row in res_data:
                                    if isinstance(row, dict):
                                        # Sisipkan info identitas dosen di kolom terdepan
                                        record = {
                                            "nama_sdm": sdm_nama,
                                            "nidn": sdm_nidn,
                                            "id_sdm": sdm_id
                                        }
                                        record.update(row)
                                        all_combined_data.append(record)
                            elif isinstance(res_data, dict) and "error" not in res_data and len(res_data) > 0:
                                success_count += 1
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
                    
                    status_text.text("🎉 Selesai memproses semua dosen!")
                    
                    if all_combined_data:
                        df_all = pd.DataFrame(all_combined_data)
                        
                        st.success(f"✅ Selesai! Berhasil menarik **{len(df_all)} baris data** dari total Dosen yang memiliki data.")
                        
                        col_m1, col_m2 = st.columns(2)
                        col_m1.metric("Total Dosen Diproses", total_sdm)
                        col_m2.metric("Total Record Ditemukan", len(df_all))
                        
                        st.dataframe(df_all, use_container_width=True)
                        
                        # Download Excel & CSV untuk gabungan seluruh dosen
                        col_d1, col_d2 = st.columns(2)
                        with col_d1:
                            buffer_all = io.BytesIO()
                            with pd.ExcelWriter(buffer_all, engine='openpyxl') as writer:
                                df_all.to_excel(writer, index=False, sheet_name=selected_cat_name[:30])
                            
                            st.download_button(
                                label=f"📊 Download SEMUA Dosen - {selected_cat_name} (.XLSX)",
                                data=buffer_all.getvalue(),
                                file_name=f"SISTER_SEMUA_DOSEN_{selected_cat_name.replace(' ', '_')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
                        with col_d2:
                            csv_bytes = df_all.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label=f"📥 Download SEMUA Dosen - {selected_cat_name} (.CSV)",
                                data=csv_bytes,
                                file_name=f"SISTER_SEMUA_DOSEN_{selected_cat_name.replace(' ', '_')}.csv",
                                mime="text/csv"
                            )
                    else:
                        st.info(f"Tidak ada data ditemukan untuk kategori `{selected_cat_name}` pada seluruh SDM.")

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
    4. **Mengunduh Data Massal (Semua Dosen):**
       - Buka tab **Tarik & Download Data**.
       - Pilih kategori data yang diinginkan (misal: Dokumen SDM, Penelitian, Pendidikan Formal, Profil).
       - Pilih **`🌐 SEMUA Dosen (Batch Download)`**.
       - Klik **Tarik Data dari API SISTER**.
       - Sistem akan otomatis melakukan perulangan untuk menarik seluruh data dosen dan menggabungkannya ke dalam 1 file Excel/CSV siap download.
    """)