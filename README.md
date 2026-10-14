# 🤖 TRO Lab Manager

Sistem manajemen laboratorium berbasis web untuk mengelola **alat, peminjaman, maintenance, jadwal, dan status laboratorium** di lingkungan Teknologi Rekayasa Otomasi. Tujuan pengembangan sebagai tugas **Vibe Coding** menggunakan Python (Flask) dan SQLite dengan kemungkinan dapat dikembangkan untuk kebutuhan Laboratorium Program Studi kedepannya

🔗 **Demo:** [https://trolabmanager.vercel.app](https://trolabmanager.vercel.app)

> Versi demo di Vercel memakai database sementara, jadi data yang diinput bisa hilang saat server restart dan upload foto dinonaktifkan. Lihat bagian [Deploy ke Vercel](#-deploy-ke-vercel).

## ✨ Fitur

- 🔐 **Login & Register** dengan tiga role: Admin, Dosen, dan Mahasiswa.
- 🏠 **Dashboard**: ringkasan jumlah alat (total, tersedia, dipinjam, maintenance, rusak), jadwal hari ini, dan aktivitas terbaru.
- 🏫 **Laboratorium**: daftar lab lengkap dengan foto, lokasi, kapasitas, dan status **Kosong / Sedang dipakai**.
  - Status ditentukan **otomatis dari jadwal**.
  - Admin dapat menimpanya secara **manual** kapan saja, dan mengembalikannya ke mode otomatis.
- 🔧 **Peralatan**: inventaris alat per laboratorium, dengan pencarian, filter status, dan foto alat.
- 📦 **Peminjaman**: alur `Diajukan → Disetujui → Dipinjam → Dikembalikan`. Status alat berubah otomatis.
- 🛠️ **Maintenance**: pencatatan perbaikan alat beserta riwayatnya.
- 📅 **Jadwal**: jadwal penggunaan laboratorium.
- ⚙️ **Settings**: nama lab, deskripsi, logo, dan foto lab.

## 👥 Hak Akses

| Fitur | Admin | Dosen & Mahasiswa |
|---|---|---|
| Dashboard | Lengkap | Ya (aktivitas hanya miliknya) |
| Laboratorium | Lihat, tambah, ubah, hapus, atur status | Hanya melihat |
| Peralatan | Lihat, tambah, ubah, hapus | Hanya melihat |
| Peminjaman | Lihat semua, setujui, ubah status | Mengajukan dan melihat peminjaman sendiri |
| Maintenance | Penuh | Hanya melihat |
| Jadwal | Tambah, hapus | Hanya melihat |
| Settings | Penuh | Tidak ada akses |

## 🛠️ Teknologi

| Bagian | Teknologi |
|---|---|
| Frontend | HTML, CSS, JavaScript (Jinja2) |
| Backend | Python, Flask |
| Database | SQLite |
| Hosting | Vercel |

## 📂 Struktur Proyek

```text
VIBE CODING/
├── BACKEND/
│   └── app.py            # aplikasi Flask (route, database, hak akses)
├── FRONTEND/
│   └── templates/        # halaman HTML (base, dashboard, labs, equipment, dst.)
├── public/
│   └── static/
│       ├── style.css     # tampilan
│       └── uploads/      # foto lab dan alat (dibuat otomatis, tidak diunggah ke Git)
├── .gitignore
├── pyproject.toml        # penunjuk entrypoint Flask untuk Vercel
├── requirements.txt
└── README.md
```

## 🚀 Cara Menjalankan (Lokal)

1. **Pastikan Python 3.10+ sudah terpasang**, lalu clone repo ini:
```bash
   git clone https://github.com/hazzataqiyhiroshi-blip/vibe-coding.git
   cd vibe-coding
```
2. **Pasang dependensi:**
```bash
   pip install -r requirements.txt
```
3. **Jalankan aplikasi:**
```bash
   python BACKEND/app.py
```
4. **Buka di browser:** [http://127.0.0.1:5000](http://127.0.0.1:5000)

Database `lab_manager.db` dibuat **otomatis** saat aplikasi pertama kali dijalankan, lengkap dengan data contoh (3 laboratorium, 4 alat, dan 1 jadwal).

## 🔑 Akun

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin |

Akun **Dosen** dan **Mahasiswa** dibuat lewat halaman **Register** dengan mengisi **Nama** dan **NIM/NIP**. Saat login, gunakan **Nama** sebagai username dan **NIM/NIP** sebagai password.

> ⚠️ Akun admin hanya untuk demo. Untuk pemakaian sungguhan, ganti password admin dan atur `SECRET_KEY` lewat environment variable.

## 🗄️ Database

Semua data disimpan di SQLite (`BACKEND/lab_manager.db`) dengan tabel berikut:

| Tabel | Isi |
|---|---|
| `users` | akun login (password disimpan sebagai hash) |
| `labs` | data laboratorium dan status manual |
| `equipment` | inventaris alat |
| `borrowings` | peminjaman, terhubung ke `equipment` dan `users` |
| `maintenance` | riwayat perawatan, terhubung ke `equipment` |
| `schedules` | jadwal penggunaan lab |
| `settings` | nama lab, logo, dan foto lab |

File foto disimpan di folder `public/static/uploads`, sedangkan database hanya mencatat nama filenya. File `lab_manager.db` dan foto upload tidak ikut diunggah ke GitHub (diatur di `.gitignore`).

## ☁️ Deploy ke Vercel

Proyek ini sudah terhubung ke Vercel dan otomatis di-deploy ulang setiap kali ada `git push` ke branch `main`.

- **Entrypoint:** `pyproject.toml` menunjuk ke `BACKEND.app:app`.
- **File statis:** CSS dan gambar berada di `public/static`, karena Vercel mengabaikan folder static bawaan Flask.
- **Environment variable:** `SECRET_KEY` diatur di *Settings → Environment Variables* pada dashboard Vercel.

**Keterbatasan versi Vercel:** filesystem Vercel bersifat sementara, sehingga database memakai `/tmp` dan dibuat ulang dengan data contoh saat server restart. Akun `admin` selalu tersedia, tetapi data yang diinput dan akun Dosen/Mahasiswa yang didaftarkan dapat hilang, dan upload foto dinonaktifkan. Untuk penyimpanan permanen, database perlu dipindah ke layanan online seperti Neon atau Turso.

## 👤 Pembuat

- **Nama:** Muhammad Hazzataqiy Hiroshi
- **NIM:** 40040326630034
- **Mata kuliah:** Praktikum Algoritma dan Pemrograman
- **Program Studi:** Teknologi Rekayasa Otomasi 2026
- **Fakultas:** Sekolah Vokasi
- **Universitas:** Universitas Diponegoro
