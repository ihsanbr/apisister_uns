# 🎓 Dashboard Konektor API SISTER Kemdiktisaintek

Aplikasi Dashboard berbasi Web (Streamlit) lokal untuk mempermudah koneksi, eksplorasi, dan pengunduhan data dari API SISTER (Sistem Informasi Sumberdaya Terpadu) Kemdiktisaintek.

---

## 🚀 Cara Menjalankan di Komputer Lokal (Windows / Mac / Linux)

### Langkah 1: Pastikan Python Sudah Terinstal
Pastikan **Python 3.8** atau versi yang lebih baru sudah terinstal di komputer Anda.
Cek via Terminal / Command Prompt:
```bash
python --version
# atau
python3 --version
```

---

### Langkah 2: Install Depedensi / Package
Buka Command Prompt (Windows) atau Terminal (Mac/Linux), masuk ke folder ini, lalu jalankan:

```bash
pip install -r requirements.txt
```

---

### Langkah 3: Jalankan Dashboard
Jalankan perintah berikut di Command Prompt / Terminal:

```bash
streamlit run app.py
```

Setelah perintah tersebut dijalankan, browser Anda akan otomatis terbuka di alamat:
👉 **`http://localhost:8501`**

---

## 📂 Struktur File Dalam Folder Ini

- `app.py` : Kode utama antarmuka pengguna (UI) Dashboard Streamlit.
- `sister_client.py` : Modul pemanggil HTTP Request API SISTER (Authorize, Query SDM, dan Data Detail).
- `requirements.txt` : Daftar pustaka Python yang dibutuhkan.
- `README.md` : Panduan penggunaan dan instalasi.

---

## 🔐 Keamanan Kredensial
Kredensial API SISTER (`Username`, `Password`, `ID Pengguna`) Anda hanya disimpan dalam memori lokal browser/session saat aplikasi berjalan dan **TIDAK** dikirim ke server pihak ketiga manapun.
