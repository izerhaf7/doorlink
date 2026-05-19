# 🚪 DoorLink — Setup Guide

Panduan untuk menyalakan **backend (FastAPI)** dan **frontend (Dashboard Admin)** DoorLink.

---

## 📋 Prasyarat

| Software | Versi Minimum | Cek Instalasi |
|----------|---------------|---------------|
| Python | 3.10+ | `python --version` |
| pip | terbaru | `pip --version` |
| Git | opsional | `git --version` |

> **Catatan:** Jika menggunakan koneksi ke MikroTik RouterOS, pastikan router dapat dijangkau dari jaringan lokal.

---

## 📁 Struktur Proyek

```
doorlink/
└── backend/
    ├── app/
    │   ├── models/          # SQLModel (User, Role, AccessLog)
    │   ├── routers/         # API + Dashboard routes
    │   ├── schemas/         # Pydantic schemas
    │   ├── services/        # Business logic
    │   ├── templates/       # Jinja2 HTML templates (Dashboard)
    │   ├── static/          # CSS assets
    │   ├── main.py          # Entry point FastAPI
    │   ├── config.py        # Environment config
    │   └── database.py      # SQLite engine & session
    ├── .env                 # Konfigurasi lokal (tidak di-commit)
    ├── .env.example         # Contoh konfigurasi
    ├── requirements.txt     # Dependensi Python
    └── doorlink.db          # SQLite database (auto-generated)
```

---

## 🔧 Langkah 1 — Clone / Buka Proyek

```bash
cd doorlink/backend
```

---

## 🔧 Langkah 2 — Buat Virtual Environment

```bash
python -m venv venv
```

Aktifkan virtual environment:

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

---

## 🔧 Langkah 3 — Install Dependensi

```bash
pip install -r requirements.txt
```

Dependensi yang akan terinstall:

| Package | Fungsi |
|---------|--------|
| `fastapi` | Web framework utama |
| `uvicorn[standard]` | ASGI server |
| `sqlmodel` | ORM (SQLAlchemy + Pydantic) |
| `jinja2` | Template engine untuk dashboard |
| `python-multipart` | Parsing form data |
| `python-dotenv` | Load file `.env` |
| `requests` | HTTP client ke MikroTik API |

---

## 🔧 Langkah 4 — Konfigurasi Environment

Salin file `.env.example` menjadi `.env`:

```bash
copy .env.example .env
```

Edit file `.env` sesuai konfigurasi:

```env
MIKROTIK_HOST=192.168.88.1
MIKROTIK_USER=admin
MIKROTIK_PASSWORD=yourpassword
DATABASE_URL=sqlite:///doorlink.db
```

> **Jika tidak punya MikroTik:** Biarkan saja default. Dashboard akan menampilkan status **Offline** tanpa crash.

---

## 🚀 Langkah 5 — Jalankan Server

```bash
uvicorn app.main:app --reload
```

Output yang diharapkan:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

> Flag `--reload` membuat server otomatis restart saat ada perubahan file (mode development).

---

## 🌐 Mengakses Aplikasi

### Frontend — Dashboard Admin

| Halaman | URL |
|---------|-----|
| 🏠 Dashboard Home | [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard) |
| 👥 User Management | [http://127.0.0.1:8000/dashboard/users](http://127.0.0.1:8000/dashboard/users) |
| 📋 Access Logs | [http://127.0.0.1:8000/dashboard/logs](http://127.0.0.1:8000/dashboard/logs) |
| 🚪 Door Simulation | [http://127.0.0.1:8000/dashboard/door](http://127.0.0.1:8000/dashboard/door) |

### Backend — API Endpoints

| Endpoint | URL |
|----------|-----|
| Root | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) |
| Swagger Docs | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| ReDoc | [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc) |

### API Endpoint Lengkap

| Method | Endpoint | Fungsi |
|--------|----------|--------|
| GET | `/` | Status server |
| GET | `/roles` | Daftar semua role |
| GET | `/users/` | Daftar semua user |
| GET | `/users/{username}` | Detail user |
| POST | `/users/` | Buat user baru |
| DELETE | `/users/{username}` | Hapus user |
| GET | `/access/check-door/{username}` | Cek akses pintu |
| POST | `/access/open-door/{username}` | Simulasi buka pintu |
| GET | `/access/logs` | Semua access log |
| GET | `/hotspot/users` | Daftar user hotspot |
| GET | `/hotspot/active` | Session hotspot aktif |
| GET | `/mikrotik/resource` | Info resource MikroTik |
| GET | `/esp32/check-access/{username}` | Endpoint khusus ESP32 |

---

## 🛑 Menghentikan Server

Tekan `Ctrl + C` di terminal untuk menghentikan uvicorn.

Untuk menonaktifkan virtual environment:

```bash
deactivate
```

---

## ❓ Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `ModuleNotFoundError` | Pastikan virtual environment aktif dan jalankan `pip install -r requirements.txt` |
| MikroTik status Offline | Normal jika tidak ada router. Dashboard tetap berjalan. |
| Port 8000 sudah dipakai | Jalankan dengan port lain: `uvicorn app.main:app --reload --port 8001` |
| Database error | Hapus `doorlink.db`, lalu restart server — database akan dibuat ulang otomatis |
| Template error 500 | Pastikan folder `app/templates/` dan `app/static/` ada beserta isinya |
