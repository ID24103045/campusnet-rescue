#!/usr/bin/env python3
"""Member 3 solver for CNR-05: unzip, verify hashes, normalise all time zones to UTC, correlate
auth.log + browser History + bodyfile inside the Stage-4 window, build the flag.
Usage: python3 solvers/m3_solve_stage5.py [evidence_package.zip]"""
import sys, re, zipfile, hashlib, sqlite3, tempfile, pathlib, datetime as dt, csv, io
zp = sys.argv[1] if len(sys.argv) > 1 else str(pathlib.Path(__file__).resolve().parents[1] / "dist/cnr-05/evidence_package.zip")
UTC, LOCAL = dt.timezone.utc, dt.timezone(dt.timedelta(hours=5, minutes=30))
W0, W1 = dt.datetime(2026, 3, 14, 9, 30, tzinfo=UTC), dt.datetime(2026, 3, 14, 10, 15, tzinfo=UTC)
z = zipfile.ZipFile(zp)
man = dict(reversed(l.split("  ", 1)) for l in z.read("MANIFEST.sha256").decode().splitlines())
for n, h in man.items(): assert hashlib.sha256(z.read(n)).hexdigest() == h, n
print("[ok] manifest hashes verified")
# 1. auth.log (local time) -> UTC, find ACCEPTED logins in window whose source is not a known admin host
logins = []
for l in z.read("logs/auth.log").decode().splitlines():
    m = re.match(r"(\w{3} \d+ [\d:]{8}) \S+ sshd\[\d+\]: Accepted \w+ for (\S+) from (\S+)", l)
    if m:
        t = dt.datetime.strptime("2026 " + m.group(1), "%Y %b %d %H:%M:%S").replace(tzinfo=LOCAL).astimezone(UTC)
        if W0 <= t <= W1: logins.append((t, m.group(2), m.group(3)))
print("logins in window (UTC):", [(t.strftime("%H:%M:%S"), u, ip) for t, u, ip in logins])
# 2. browser history: visits to the portal inside the window, per profile
def visits(name):
    with tempfile.NamedTemporaryFile() as f:
        f.write(z.read(name)); f.flush(); con = sqlite3.connect(f.name)
        rows = con.execute("select u.url, v.visit_time from visits v join urls u on u.id=v.url").fetchall()
    return [(url, dt.datetime(1601, 1, 1, tzinfo=UTC) + dt.timedelta(microseconds=t)) for url, t in rows]
cands = []
for t, user, ip in logins:
    portal = [(u, vt) for u, vt in visits(f"browser/{user}/History") if "lantern-gate" in u and W0 <= vt <= W1] if f"browser/{user}/History" in z.namelist() else []
    if portal: cands.append((t, user, ip, portal))
assert len(cands) == 1, cands
t, user, ip, portal = cands[0]
# 3. bodyfile: new file created by that user after the portal visit
rows = list(csv.DictReader(io.StringIO(z.read("fs/bodyfile.csv").decode())))
after = [r for r in rows if r["owner"] == user and portal[0][1] <= dt.datetime.fromtimestamp(int(r["mtime_utc_epoch"]), UTC) <= W1 and r["path"].endswith(".zip")]
art = pathlib.PurePosixPath(after[0]["path"]).name
print(f"account={user} src={ip} portal_visit={portal[0][1].time()} artefact={art}")
print("FLAG: IE3132{%s_%s_%s}" % (user, art.lower().replace(".", "-").replace("_", "-"), t.strftime("%Y%m%dT%H%M%SZ")))
