# 🤖 TRO Lab Manager

Sistem manajemen laboratorium berbasis web untuk mengelola **alat, peminjaman, maintenance, jadwal, dan status laboratorium** di lingkungan Teknologi Rekayasa Otomasi. Dibuat sebagai tugas **Vibe Coding** menggunakan Python (Flask) dan SQLite.

## ✨ Fitur

- 🔐 **Login & Register** dengan tiga role: Admin, Dosen, dan Mahasiswa.
- 🏠 **Dashboard**: ringkasan jumlah alat (total, tersedia, dipinjam, maintenance, rusak), jadwal hari ini, dan aktivitas terbaru.
- 🏫 **Laboratorium**: daftar lab lengkap dengan foto, lokasi, kapasitas, dan status **Kosong / Sedang dipakai**.
  - Status ditentukan **otomatis dari jadwal**.
  - Admin dapat menimpanya secara **manual** dengan masa berlaku (sampai jadwal berubah, 1 jam, sampai akhir hari, atau sampai diubah lagi).
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
| Frontend | HTML, CSS, JavaScript (template Jinja2) |
| Backend | Python, Flask |
| Database | SQLite |

## 📂 Struktur Proyek

```text
VIBE CODING/
├── BACKEND/
│   └── app.py            # aplikasi Flask (route, database, hak akses)
├── FRONTEND/
│   ├── templates/        # halaman HTML (base, dashboard, labs, equipment, dst.)
│   └── static/
│       ├── style.css     # tampilan
│       └── uploads/      # foto lab dan alat (dibuat otomatis)
├── requirements.txt
└── README.md
```

## 🚀 Cara Menjalankan

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

## 🔑 Akun Bawaan

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Admin |

> ⚠️ Akun ini hanya untuk demo. Ganti password dan `secret_key` di `BACKEND/app.py` sebelum dipakai sungguhan.

Akun Dosen dan Mahasiswa dibuat lewat halaman **Register**.

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

File foto disimpan di folder `FRONTEND/static/uploads`, sedangkan database hanya mencatat nama filenya.

## 📸 Tampilan

<!-- Tambahkan screenshot di sini, contoh: -->
<!-- ![Dashboard](docs/dashboard.png) -->

## 👤 Pembuat

- **Nama:** Muhammad Hazzataqiy Hiroshi
- **NIM:** 40040326630034
- **Mata kuliah:** Algoritma dan Pemrograman (Vibe Coding)
- **Program Studi:** Teknologi Rekayasa Otomasi 2026
- **Fakultas:** Sekolah Vokasi
- **Universitas:** Universitas Diponegoro