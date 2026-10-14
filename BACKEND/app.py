import os, sqlite3, time
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, g, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

IS_VERCEL = bool(os.environ.get("VERCEL"))
BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, ".."))
PUBLIC = os.path.join(ROOT, "public")

if IS_VERCEL:
    DB = "/tmp/lab_manager.db"
    UPLOAD = "/tmp/uploads"
else:
    DB = os.path.join(BASE, "lab_manager.db")
    UPLOAD = os.path.join(PUBLIC, "static", "uploads")
    os.makedirs(UPLOAD, exist_ok=True)

app = Flask(__name__,
            template_folder=os.path.join(ROOT, "FRONTEND", "templates"),
            static_folder=os.path.join(PUBLIC, "static"))
app.secret_key = os.environ.get("SECRET_KEY", "tro-lab-manager")

# Aksi yang hanya boleh dilakukan Admin
# (halaman maintenance, jadwal, dan laboratorium boleh DILIHAT semua role)
ADMIN_ONLY = {
    "equipment_add", "equipment_update", "equipment_delete",
    "borrowing_next",
    "maintenance_add", "maintenance_done",
    "schedule_add", "schedule_delete",
    "lab_add", "lab_update", "lab_delete", "lab_status",
    "settings",
}

# ---------- Database ----------
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    d = g.pop("db", None)
    if d:
        d.close()

def q(sql, args=(), one=False):
    rows = db().execute(sql, args).fetchall()
    return (rows[0] if rows else None) if one else rows

def run(sql, args=()):
    db().execute(sql, args)
    db().commit()

def is_admin():
    return session.get("role") == "Admin"

def init_db():
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT, role TEXT, password TEXT);
    CREATE TABLE IF NOT EXISTS equipment(id INTEGER PRIMARY KEY, kode TEXT, nama TEXT, kategori TEXT,
        merk TEXT, model TEXT, serial TEXT, lokasi TEXT, kondisi TEXT, status TEXT, foto TEXT, tgl_beli TEXT);
    CREATE TABLE IF NOT EXISTS borrowings(id INTEGER PRIMARY KEY, equipment_id INTEGER, username TEXT, nama TEXT,
        nim TEXT, jumlah INTEGER, tanggal TEXT, keperluan TEXT, status TEXT);
    CREATE TABLE IF NOT EXISTS maintenance(id INTEGER PRIMARY KEY, equipment_id INTEGER, tanggal TEXT,
        masalah TEXT, teknisi TEXT, status TEXT);
    CREATE TABLE IF NOT EXISTS schedules(id INTEGER PRIMARY KEY, tanggal TEXT, mulai TEXT, selesai TEXT,
        kegiatan TEXT, ruang TEXT);
    CREATE TABLE IF NOT EXISTS labs(id INTEGER PRIMARY KEY, nama TEXT, lokasi TEXT, kapasitas INTEGER,
        deskripsi TEXT, foto TEXT, status_manual TEXT);
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    """)
    if not con.execute("SELECT 1 FROM settings").fetchone():
        con.executemany("INSERT INTO settings VALUES(?,?)", [
            ("nama_lab", "Laboratorium Teknologi Rekayasa Otomasi"),
            ("deskripsi", "Pengelolaan alat, peminjaman, maintenance, dan jadwal laboratorium.")])
    if not con.execute("SELECT 1 FROM equipment").fetchone():
        t = date.today().isoformat()
        con.executemany("""INSERT INTO equipment(kode,nama,kategori,merk,model,serial,lokasi,kondisi,status,tgl_beli)
            VALUES(?,?,?,?,?,?,?,?,?,?)""", [
            ("EQ001", "Digital Oscilloscope", "Measurement", "-", "-", "-", "Lab Elektronika", "Baik", "Tersedia", t),
            ("EQ002", "Multimeter", "Measurement", "-", "-", "-", "Lab Elektronika", "Baik", "Tersedia", t),
            ("EQ003", "PLC Trainer", "Automation", "-", "-", "-", "Lab Otomasi", "Baik", "Tersedia", t),
            ("EQ004", "Power Supply DC", "Power", "-", "-", "-", "Lab Elektronika", "Baik", "Tersedia", t)])
        con.execute("INSERT INTO schedules(tanggal,mulai,selesai,kegiatan,ruang) VALUES(?,?,?,?,?)",
                    (t, "10:00", "12:00", "Praktikum Elektronika", "Lab Elektronika"))
    if not con.execute("SELECT 1 FROM labs").fetchone():
        con.executemany("INSERT INTO labs(nama,lokasi,kapasitas,deskripsi) VALUES(?,?,?,?)", [
            ("Lab Elektronika", "Gedung Teknik Lt. 1", 30, "Praktikum elektronika analog dan digital."),
            ("Lab Otomasi", "Gedung Teknik Lt. 2", 24, "Praktikum PLC dan sistem kontrol."),
            ("Lab Komputer", "Gedung Teknik Lt. 1", 40, "Praktikum pemrograman dan algoritma.")])

    # Migrasi database lama
    ucols = [r[1] for r in con.execute("PRAGMA table_info(users)")]
    if "password" not in ucols:
        con.execute("ALTER TABLE users ADD COLUMN password TEXT")
    bcols = [r[1] for r in con.execute("PRAGMA table_info(borrowings)")]
    if "username" not in bcols:
        con.execute("ALTER TABLE borrowings ADD COLUMN username TEXT")
    lcols = [r[1] for r in con.execute("PRAGMA table_info(labs)")]
    if "status_manual" not in lcols:
        con.execute("ALTER TABLE labs ADD COLUMN status_manual TEXT")

    admin = con.execute("SELECT id, password FROM users WHERE username='admin'").fetchone()
    if not admin:
        con.execute("INSERT INTO users(username,role,password) VALUES('admin','Admin',?)",
                    (generate_password_hash("admin123"),))
    elif not admin[1]:
        con.execute("UPDATE users SET password=? WHERE id=?", (generate_password_hash("admin123"), admin[0]))

    con.commit(); con.close()

def save_file(f):
    if IS_VERCEL:
        return None
    if f and f.filename:
        name = f"{int(time.time())}_{secure_filename(f.filename)}"
        f.save(os.path.join(UPLOAD, name))
        return name
    return None

@app.context_processor
def inject_settings():
    return {"S": {r["key"]: r["value"] for r in q("SELECT * FROM settings")}}

# ---------- Login, Register, Logout & Hak Akses ----------
@app.before_request
def require_login():
    ep = request.endpoint
    if ep in ("login", "register", "static"):
        return
    if not session.get("user"):
        return redirect(url_for("login"))
    if ep in ADMIN_ONLY and not is_admin():
        flash("Akses ditolak: aksi ini hanya untuk Admin.", "err")
        return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        u = q("SELECT * FROM users WHERE username=?", (request.form["username"].strip(),), one=True)
        if u and u["password"] and check_password_hash(u["password"], request.form["password"]):
            session["user"] = u["username"]
            session["role"] = u["role"]
            return redirect(url_for("dashboard"))
        flash("Username atau password salah.", "err")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        nim = request.form.get("nim", "").strip()
        nim2 = request.form.get("nim2", "").strip()
        role = request.form.get("role", "Mahasiswa")
        if role not in ("Mahasiswa", "Dosen"):
            role = "Mahasiswa"
        if not nama or not nim:
            flash("Nama dan NIM/NIP wajib diisi.", "err")
        elif len(nim) < 6:
            flash("NIM/NIP minimal 6 karakter.", "err")
        elif nim != nim2:
            flash("Konfirmasi NIM/NIP tidak sama.", "err")
        elif q(
            "SELECT 1 FROM users WHERE username=?",
            (nama,),
            one=True
        ):
            flash("Nama sudah terdaftar. Silakan login.", "err")
        else:
            run(
                "INSERT INTO users(username, role, password) "
                "VALUES(?,?,?)",
                (nama, role, generate_password_hash(nim))
            )
            flash("Registrasi berhasil. Silakan login.")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Anda berhasil logout.")
    return redirect(url_for("login"))

# ---------- Dashboard ----------
@app.route("/")
def dashboard():
    count = lambda st: q("SELECT COUNT(*) c FROM equipment WHERE status=?", (st,), one=True)["c"]
    stats = {"total": q("SELECT COUNT(*) c FROM equipment", one=True)["c"],
             "tersedia": count("Tersedia"), "dipinjam": count("Dipinjam"),
             "maintenance": count("Maintenance"), "rusak": count("Rusak")}
    today = q("SELECT * FROM schedules WHERE tanggal=? ORDER BY mulai", (date.today().isoformat(),))
    base = "SELECT b.*, e.nama alat FROM borrowings b JOIN equipment e ON e.id=b.equipment_id"
    if is_admin():
        act = [f"📦 {b['nama']} - {b['alat']} ({b['status']})" for b in q(base + " ORDER BY b.id DESC LIMIT 4")]
        act += [f"🛠️ {m['alat']} - {m['masalah']} ({m['status']})" for m in q(
            "SELECT m.*, e.nama alat FROM maintenance m JOIN equipment e ON e.id=m.equipment_id ORDER BY m.id DESC LIMIT 4")]
    else:
        act = [f"📦 {b['alat']} ({b['status']})" for b in q(
            base + " WHERE b.username=? ORDER BY b.id DESC LIMIT 5", (session["user"],))]
    return render_template("dashboard.html", stats=stats, today=today, act=act)

# ---------- Laboratorium ----------
@app.route("/labs")
def labs():
    now = datetime.now()
    today, hm = now.strftime("%Y-%m-%d"), now.strftime("%H:%M")
    data = []
    for l in q("SELECT * FROM labs ORDER BY nama"):
        cur = q("""SELECT * FROM schedules WHERE ruang=? AND tanggal=? AND mulai<=? AND selesai>?
                   ORDER BY mulai""", (l["nama"], today, hm, hm), one=True)
        nxt = q("""SELECT * FROM schedules WHERE ruang=? AND tanggal=? AND mulai>?
                   ORDER BY mulai""", (l["nama"], today, hm), one=True)
        manual = l["status_manual"]          # None = otomatis dari jadwal
        status = manual if manual else ("Sedang dipakai" if cur else "Kosong")
        data.append({"lab": l, "cur": cur, "nxt": nxt, "status": status, "manual": manual})
    return render_template("labs.html", data=data)

@app.route("/labs/add", methods=["POST"])
def lab_add():
    f = request.form
    run("INSERT INTO labs(nama,lokasi,kapasitas,deskripsi,foto) VALUES(?,?,?,?,?)",
        (f["nama"], f["lokasi"], f["kapasitas"] or 0, f["deskripsi"], save_file(request.files.get("foto"))))
    flash("Laboratorium ditambahkan."); return redirect(url_for("labs"))

@app.route("/labs/<int:i>/update", methods=["POST"])
def lab_update(i):
    f = request.form
    run("UPDATE labs SET kapasitas=?, deskripsi=? WHERE id=?", (f["kapasitas"] or 0, f["deskripsi"], i))
    foto = save_file(request.files.get("foto"))
    if foto:
        run("UPDATE labs SET foto=? WHERE id=?", (foto, i))
    flash("Laboratorium diperbarui."); return redirect(url_for("labs"))

@app.route("/labs/<int:i>/status", methods=["POST"])
def lab_status(i):
    s = request.form.get("status")
    if s not in ("Kosong", "Sedang dipakai"):
        s = None                              # "Otomatis" -> kembali ke jadwal
    run("UPDATE labs SET status_manual=? WHERE id=?", (s, i))
    flash("Status lab diperbarui."); return redirect(url_for("labs"))

@app.route("/labs/<int:i>/delete", methods=["POST"])
def lab_delete(i):
    run("DELETE FROM labs WHERE id=?", (i,))
    flash("Laboratorium dihapus."); return redirect(url_for("labs"))

# ---------- Equipment ----------

# ---------- Equipment ----------
@app.route("/equipment")
def equipment():
    lab = request.args.get("lab", "").strip()
    kw, st = request.args.get("q", ""), request.args.get("status", "")

    # Nama lab = gabungan tabel labs dan lokasi alat yang sudah ada
    names = {r["nama"] for r in q("SELECT nama FROM labs")}
    names |= {r["lokasi"] for r in q("SELECT DISTINCT lokasi FROM equipment") if r["lokasi"]}
    labs = sorted(names)
    lab_counts = {r["lokasi"]: r["c"] for r in q("SELECT lokasi, COUNT(*) c FROM equipment GROUP BY lokasi")}

    items = []
    if lab:
        sql = "SELECT * FROM equipment WHERE lokasi=? AND (nama LIKE ? OR kode LIKE ?)"
        args = [lab, f"%{kw}%", f"%{kw}%"]
        if st:
            sql += " AND status=?"; args.append(st)
        items = q(sql + " ORDER BY kode", args)

    return render_template("equipment.html", labs=labs, lab_counts=lab_counts,
                           items=items, kw=kw, st=st)

@app.route("/equipment/add", methods=["POST"])
def equipment_add():
    f = request.form
    run("""INSERT INTO equipment(kode,nama,kategori,merk,model,serial,lokasi,kondisi,status,foto,tgl_beli)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (f["kode"], f["nama"], f["kategori"], f["merk"], f["model"], f["serial"], f["lokasi"],
         f["kondisi"], "Tersedia", save_file(request.files.get("foto")), f["tgl_beli"]))
    flash("Alat ditambahkan.")
    return redirect(url_for("equipment", lab=f["lokasi"]))

@app.route("/equipment/<int:i>/update", methods=["POST"])
def equipment_update(i):
    e = q("SELECT lokasi FROM equipment WHERE id=?", (i,), one=True)
    run("UPDATE equipment SET status=?, kondisi=? WHERE id=?", (request.form["status"], request.form["kondisi"], i))
    foto = save_file(request.files.get("foto"))
    if foto:
        run("UPDATE equipment SET foto=? WHERE id=?", (foto, i))
    flash("Alat diperbarui.")
    return redirect(url_for("equipment", lab=e["lokasi"] if e else ""))

@app.route("/equipment/<int:i>/delete", methods=["POST"])
def equipment_delete(i):
    e = q("SELECT lokasi FROM equipment WHERE id=?", (i,), one=True)
    run("DELETE FROM equipment WHERE id=?", (i,))
    flash("Alat dihapus.")
    return redirect(url_for("equipment", lab=e["lokasi"] if e else ""))

# ---------- Peminjaman ----------
FLOW = {"Diajukan": "Disetujui", "Disetujui": "Dipinjam", "Dipinjam": "Dikembalikan"}

@app.route("/borrowing")
def borrowing():
    base = "SELECT b.*, e.nama alat FROM borrowings b JOIN equipment e ON e.id=b.equipment_id"
    if is_admin():
        rows = q(base + " ORDER BY b.id DESC")
    else:
        rows = q(base + " WHERE b.username=? ORDER BY b.id DESC", (session["user"],))
    return render_template("borrowing.html", rows=rows, flow=FLOW,
                           avail=q("SELECT * FROM equipment WHERE status='Tersedia' ORDER BY nama"))

@app.route("/borrowing/add", methods=["POST"])
def borrowing_add():
    f = request.form
    run("""INSERT INTO borrowings(equipment_id,username,nama,nim,jumlah,tanggal,keperluan,status)
           VALUES(?,?,?,?,?,?,?,?)""",
        (f["equipment_id"], session["user"], f["nama"], f["nim"], f["jumlah"], f["tanggal"], f["keperluan"], "Diajukan"))
    flash("Pengajuan peminjaman dibuat."); return redirect(url_for("borrowing"))

@app.route("/borrowing/<int:i>/next", methods=["POST"])
def borrowing_next(i):
    b = q("SELECT * FROM borrowings WHERE id=?", (i,), one=True)
    if b and b["status"] in FLOW:
        new = FLOW[b["status"]]
        run("UPDATE borrowings SET status=? WHERE id=?", (new, i))
        if new == "Dipinjam":
            run("UPDATE equipment SET status='Dipinjam' WHERE id=?", (b["equipment_id"],))
        elif new == "Dikembalikan":
            run("UPDATE equipment SET status='Tersedia' WHERE id=?", (b["equipment_id"],))
    return redirect(url_for("borrowing"))

# ---------- Maintenance ----------
@app.route("/maintenance")
def maintenance():
    rows = q("SELECT m.*, e.nama alat FROM maintenance m JOIN equipment e ON e.id=m.equipment_id ORDER BY m.id DESC")
    return render_template("maintenance.html", rows=rows, items=q("SELECT * FROM equipment ORDER BY nama"))

@app.route("/maintenance/add", methods=["POST"])
def maintenance_add():
    f = request.form
    run("INSERT INTO maintenance(equipment_id,tanggal,masalah,teknisi,status) VALUES(?,?,?,?,?)",
        (f["equipment_id"], f["tanggal"], f["masalah"], f["teknisi"], "Dalam perbaikan"))
    run("UPDATE equipment SET status='Maintenance' WHERE id=?", (f["equipment_id"],))
    flash("Maintenance dicatat."); return redirect(url_for("maintenance"))

@app.route("/maintenance/<int:i>/done", methods=["POST"])
def maintenance_done(i):
    m = q("SELECT * FROM maintenance WHERE id=?", (i,), one=True)
    if m:
        run("UPDATE maintenance SET status='Selesai' WHERE id=?", (i,))
        run("UPDATE equipment SET status='Tersedia', kondisi='Baik' WHERE id=?", (m["equipment_id"],))
    return redirect(url_for("maintenance"))

# ---------- Jadwal ----------
@app.route("/schedule")
def schedule():
    return render_template("schedule.html",
                           rows=q("SELECT * FROM schedules ORDER BY tanggal, mulai"),
                           labs=q("SELECT nama FROM labs ORDER BY nama"))

@app.route("/schedule/add", methods=["POST"])
def schedule_add():
    f = request.form
    run("INSERT INTO schedules(tanggal,mulai,selesai,kegiatan,ruang) VALUES(?,?,?,?,?)",
        (f["tanggal"], f["mulai"], f["selesai"], f["kegiatan"], f["ruang"]))
    flash("Jadwal ditambahkan."); return redirect(url_for("schedule"))

@app.route("/schedule/<int:i>/delete", methods=["POST"])
def schedule_delete(i):
    run("DELETE FROM schedules WHERE id=?", (i,))
    return redirect(url_for("schedule"))

# ---------- Settings ----------
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        run("REPLACE INTO settings VALUES('nama_lab',?)", (request.form["nama_lab"],))
        run("REPLACE INTO settings VALUES('deskripsi',?)", (request.form["deskripsi"],))
        for field in ("logo", "foto_lab"):
            name = save_file(request.files.get(field))
            if name:
                run("REPLACE INTO settings VALUES(?,?)", (field, name))
        flash("Pengaturan disimpan."); return redirect(url_for("settings"))
    return render_template("settings.html")

init_db()

if __name__ == "__main__":
    app.run(debug=True)