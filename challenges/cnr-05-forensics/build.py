#!/usr/bin/env python3
"""CNR-05 builder (Member 3). Builds dist/cnr-05/evidence_package.zip (synthetic evidence).
Timezone traps (documented in README_EVIDENCE.txt): auth.log = Asia/Colombo (UTC+05:30),
browser History = WebKit microseconds since 1601-01-01 UTC, bodyfile = UTC epoch seconds."""
import json, pathlib, sqlite3, random, zipfile, hashlib, tempfile, datetime as dt

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "dist" / "cnr-05"; OUT.mkdir(parents=True, exist_ok=True)
P = json.load(open(ROOT / "author" / "flags.json"))["params"]
random.seed(1403)
UTC = dt.timezone.utc
LOCAL = dt.timezone(dt.timedelta(hours=5, minutes=30))
def U(h, m, s, day=14): return dt.datetime(2026, 3, day, h, m, s, tzinfo=UTC)
def webkit(t): return int((t - dt.datetime(1601, 1, 1, tzinfo=UTC)).total_seconds() * 1_000_000)

# ---------- auth.log (local time) ----------
events = []   # (utc_time, text)
def add(t, msg): events.append((t, msg))
users = ["rkumar", "lperera", "svc_backup", "nwickrama"]
for i in range(70):  # background noise through the day
    t = U(2, 0, 0) + dt.timedelta(minutes=random.randint(0, 17 * 60))
    u = random.choice(users); pid = random.randint(2000, 9000)
    kind = random.choice(["ok", "ok", "cron", "sudo"])
    if kind == "ok": add(t, f"sshd[{pid}]: Accepted publickey for {u} from 10.50.0.{random.choice([12,15,18,21])} port {random.randint(40000,60000)} ssh2")
    elif kind == "cron": add(t, f"CRON[{pid}]: pam_unix(cron:session): session opened for user {u}(uid=1001) by (uid=0)")
    else: add(t, f"sudo: {u} : TTY=pts/0 ; PWD=/home/{u} ; USER=root ; COMMAND=/usr/bin/apt update")
# decoy inside the window: rkumar fails twice then logs in from the NORMAL admin host
add(U(9, 31, 2),  "sshd[4410]: Failed password for rkumar from 10.50.0.15 port 50111 ssh2")
add(U(9, 31, 9),  "sshd[4410]: Accepted password for rkumar from 10.50.0.15 port 50111 ssh2")
# tmendis normal morning login
add(U(2, 35, 40), "sshd[3102]: Accepted publickey for tmendis from 10.50.0.18 port 44120 ssh2")
# THE incident: brute-ish attempts then success from an unknown host
add(U(9, 51, 58), "sshd[4871]: Failed password for tmendis from 10.50.0.77 port 51520 ssh2")
add(U(9, 52, 5),  "sshd[4871]: Failed password for tmendis from 10.50.0.77 port 51520 ssh2")
add(U(9, 52, 17), "sshd[4875]: Accepted password for tmendis from 10.50.0.77 port 51522 ssh2")
add(U(9, 52, 18), "systemd-logind[701]: New session 41 of user tmendis.")
add(U(10, 4, 11), "sshd[4875]: pam_unix(sshd:session): session closed for user tmendis")
events.sort()
auth = "".join(f"{t.astimezone(LOCAL).strftime('%b %d %H:%M:%S')} labpc01 {m}\n" for t, m in events)

# ---------- browser histories ----------
def make_history(path, rows):
    con = sqlite3.connect(path)
    con.executescript("CREATE TABLE urls(id INTEGER PRIMARY KEY,url TEXT,title TEXT,visit_count INTEGER,last_visit_time INTEGER);"
                      "CREATE TABLE visits(id INTEGER PRIMARY KEY,url INTEGER,visit_time INTEGER);")
    for i, (t, url, title) in enumerate(rows, 1):
        con.execute("INSERT INTO urls VALUES(?,?,?,?,?)", (i, url, title, 1, webkit(t)))
        con.execute("INSERT INTO visits VALUES(?,?,?)", (i, i, webkit(t)))
    con.commit(); con.close()
tmp = pathlib.Path(tempfile.mkdtemp())
make_history(tmp / "tm_History", [
    (U(2, 40, 0),  "https://learn.lakeview.invalid/timetable", "Timetable"),
    (U(3, 10, 0),  "https://news.lakeview.invalid/", "Campus News"),
    (U(9, 53, 40), "http://10.50.0.30:8081/legacy/lantern-gate", "Lakeview Training Portal (legacy)"),
    (U(9, 54, 12), "http://10.50.0.30:8081/legacy/lantern-gate/records/restricted", "Lakeview Training Portal (legacy)"),
])
make_history(tmp / "rk_History", [
    (U(9, 33, 0),  "https://learn.lakeview.invalid/modules", "Modules"),
    (U(9, 40, 30), "https://mail.lakeview.invalid/", "Webmail"),
    (U(11, 0, 0),  "http://10.50.0.30:8081/healthz", "Portal health"),
])

# ---------- filesystem bodyfile (UTC epoch) ----------
def ep(t): return int(t.timestamp())
files = [("/home/tmendis/Documents/lantern_dataset.zip", 48211, U(9, 55, 2), "tmendis"),
         ("/home/tmendis/Documents/timetable.pdf", 20480, U(2, 41, 0), "tmendis"),
         ("/home/rkumar/Documents/lantern_dataset_old.zip", 47110, U(0, 0, 0, 10), "rkumar"),
         ("/home/rkumar/Documents/grades_draft.xlsx", 15330, U(9, 38, 11), "rkumar"),
         ("/tmp/.cache_a81", 1024, U(9, 56, 20), "tmendis")]
for i in range(45):
    owner = random.choice(["rkumar", "lperera", "nwickrama", "tmendis"])
    files.append((f"/home/{owner}/work/file_{i:02d}.txt", random.randint(100, 9000),
                  U(0, 0, 0, 12) + dt.timedelta(minutes=random.randint(0, 3000)), owner))
body = "path,size,mtime_utc_epoch,owner\n" + "".join(f"{p},{s},{ep(t)},{o}\n" for p, s, t, o in files)

README = """CAMPUSNET RESCUE - EVIDENCE PACKAGE (SYNTHETIC)
Workstation: labpc01 (fictional). All data is fabricated for the CTF.
Notes from the evidence handler:
 - logs/auth.log uses the workstation local time zone: Asia/Colombo (UTC+05:30), no year shown (year is 2026).
 - browser/*/History are SQLite files; timestamps are microseconds since 1601-01-01 00:00:00 UTC.
 - fs/bodyfile.csv timestamps are UTC epoch seconds.
Question: which account was used for the suspicious portal activity, which artefact did it produce,
and when did the suspicious session begin?
Flag format: IE3132{account_artefact_YYYYMMDDTHHMMSSZ}
 - account: lowercase login name
 - artefact: lowercase file name with every '.' and '_' replaced by '-'
 - time: the moment the suspicious session was ACCEPTED, in UTC
"""
members = {"logs/auth.log": auth, "fs/bodyfile.csv": body, "README_EVIDENCE.txt": README}
manifest = {}
zpath = OUT / "evidence_package.zip"
if zpath.exists(): zpath.unlink()
FIXED = (2026, 3, 14, 12, 0, 0)  # deterministic zip timestamps -> stable hash
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    def put(name, data):
        zi = zipfile.ZipInfo(name, FIXED); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o444 << 16
        z.writestr(zi, data); manifest[name] = hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()
    for n, d in members.items(): put(n, d)
    put("browser/tmendis/History", (tmp / "tm_History").read_bytes())
    put("browser/rkumar/History", (tmp / "rk_History").read_bytes())
    put("MANIFEST.sha256", "".join(f"{h}  {n}\n" for n, h in manifest.items()))
print("CNR-05 built ->", zpath, hashlib.sha256(zpath.read_bytes()).hexdigest())
