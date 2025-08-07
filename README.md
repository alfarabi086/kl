# 🐍 Django Project Setup

## 📋 Requirements

- Python 3.10.18  
- Virtual environment (recommended)

## 🚀 Setup Instructions

1. **Aktifkan virtual environment**  
   Pastikan Anda sudah mengaktifkan virtual environment:

   ```bash
   # Jika belum buat environment
   python -m venv venv
   # Aktifkan (Windows)
   venv\Scripts\activate
   # Aktifkan (Mac/Linux)
   source venv/bin/activate
   ```

2. **Install dependencies**  
   Jalankan perintah berikut:

   ```bash
   pip install -r requirements.txt
   ```

   Jika terjadi error saat install, Anda bisa install satu per satu:

   ```bash
   pip install <nama-paket>
   ```

3. **Jalankan migrasi database**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Jalankan server Django**

   ```bash
   python manage.py runserver
   ```

## ✅ Selesai!
Aplikasi Anda sekarang berjalan di: [http://127.0.0.1:8000](http://127.0.0.1:8000)
