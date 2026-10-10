#!/usr/bin/env python3
"""Member 4 - end-to-end, negative and unintended-solution tests. Writes tests/logs/test_report_<ts>.md
Usage: python3 tests/m4_e2e_test.py [--stage4 http://HOST:8081] [--ssh HOST:2222] [--ctfd https://HOST --token T]
Each check is a numbered test case (TC-xx) so results can be quoted in the video."""
import argparse, base64, json, pathlib, re, subprocess, sys, zipfile, datetime as dt, requests, urllib3

ROOT = pathlib.Path(__file__).resolve().parents[1]
F = json.load(open(ROOT / "author/flags.json"))
P = F["params"]
ap = argparse.ArgumentParser()
ap.add_argument("--stage4"); ap.add_argument("--ssh"); ap.add_argument("--ctfd"); ap.add_argument("--token")
a = ap.parse_args()
urllib3.disable_warnings()
results = []


def tc(i, desc, ok, detail=""):
    results.append((i, desc, "PASS" if ok else "FAIL", detail))
    print(f"{'PASS' if ok else 'FAIL'}  {i}  {desc}  {detail}")


def run(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=60)


# ---- TC-01..03: artefact integrity + file stages solved by the official solvers ----
r = run("sha256sum", "--quiet", "-c", "manifests/SHA256SUMS")
tc("TC-01", "Artefact manifest hashes match", r.returncode == 0)
out = run(sys.executable, "solvers/m2_solve_stage1_3.py").stdout
fl = re.findall(r"FLAG: (IE3132\{[^}]+\})", out)
tc("TC-02", "Stages 1-3 solver reproduces all three flags", fl == [F["cnr01"], F["cnr02"], F["cnr03"]], str(fl))
out5 = run(sys.executable, "solvers/m3_solve_stage5.py").stdout
tc("TC-03", "Stage 5 timeline solver reproduces flag", F["cnr05"] in out5)

# ---- TC-10..: unintended-shortcut checks on participant files ----
blob = b""
for p in (ROOT / "dist").rglob("*"):
    if p.is_file():
        blob += p.read_bytes()
        if p.suffix == ".zip":
            z = zipfile.ZipFile(p)
            for n in z.namelist():
                blob += z.read(n)
leaks = [k for k in ("cnr01", "cnr02", "cnr03", "cnr04", "cnr05", "cnr06") if F[k].encode() in blob]
tc("TC-10", "No real flag appears in any distributed file (raw search)", not leaks, f"leaks={leaks}")
tc("TC-11", "Stage 1: lab code absent from HTML (only in PDF metadata)",
   all(P["lab_code"] not in p.read_text() for p in (ROOT / "dist/cnr-01").glob("*.html")))
s = run("strings", "dist/cnr-02/campus_news.jpg").stdout
tc("TC-12", "Stage 2: note content/key not recoverable via strings", P["stego_note_tag"] not in s and P["vigenere_key"] not in s)
tc("TC-13", "Stage 2: wrong passphrase fails extraction",
   run("steghide", "extract", "-sf", "dist/cnr-02/campus_news.jpg", "-p", "WRONG-1234", "-xf", "/tmp/_x", "-f", "-q").returncode != 0)
b64 = (ROOT / "dist/cnr-03/wifi_notice.txt").read_text().strip().splitlines()[-1]
tc("TC-14", "Stage 3: base64 alone does not reveal portal/token", P["portal_token"].encode() not in base64.b64decode(b64))
src = (ROOT / "challenges/cnr-04-web/app/app.py").read_text()
tc("TC-15", "Stage 4 source contains no flag literal", F["cnr04"] not in src and "IE3132{" not in src)
tc("TC-16", "Stage 5: exactly one in-window login has portal+file evidence (no alternate answer)", "FLAG:" in out5)

# ---- Stage 4 live tests (positive + negative) ----
if a.stage4:
    G = a.stage4.rstrip("/") + "/legacy/lantern-gate"
    tc("TC-20", "Stage 4: restricted page denied without session", requests.get(G + "/records/restricted").status_code == 403)
    s0 = requests.Session()
    s0.post(G, data={"portal_id": "WRONG"})
    tc("TC-21", "Stage 4: wrong portal id cannot reach form", s0.get(G + "/request", allow_redirects=False).status_code == 302)
    s0.post(G, data={"portal_id": P["portal_id"]})
    neg = [dict(student_id="S1", module="NET101", access_level="admin"),
           dict(student_id="S1", module="NET101", access_level="STAFF "),
           dict(student_id="S1;--", module="NET101", access_level="staff"),
           dict(student_id="S1", module="HACK", access_level="staff"),
           dict(student_id="S1", module="NET101", access_level="student")]
    bad = [n for n in neg if F["cnr04"] in s0.post(G + "/request", data=n, allow_redirects=True).text]
    tc("TC-22", "Stage 4: five negative inputs never expose flag", not bad, str(bad))
    sol = run(sys.executable, "solvers/m3_solve_stage4.py", a.stage4).stdout
    tc("TC-23", "Stage 4: intended path (access_level=staff) yields flag", F["cnr04"] in sol)
    body = requests.get(a.stage4.rstrip("/") + "/", allow_redirects=True).text
    tc("TC-24", "Stage 4: flag not in public HTML/JS", "IE3132" not in body)

# ---- Stage 6 live ----
if a.ssh:
    h, p = a.ssh.split(":")
    o = run(sys.executable, "solvers/m3_solve_stage6.py", "dist/cnr-06/campus_capture.pcap", h, P["lab_code"], P["portal_id"], P["incident_account"], p)
    tc("TC-30", "Stage 6: intended path (pcap -> creds -> ssh -> find/cat) yields flag", F["cnr06"] in o.stdout, o.stderr[-120:])
    import paramiko
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(h, port=int(p), username="tmendis", password=P["ssh_password"], look_for_keys=False, allow_agent=False)

    def sh(cmd):
        _, so, se = c.exec_command(cmd)
        return (so.read() + se.read()).decode()

    tc("TC-31", "Stage 6: draft file (root:root 600) unreadable", "Permission denied" in sh("cat /srv/campus-archive/exports/.incident_draft.txt"))
    tc("TC-32", "Stage 6: sudo gives no escalation", "tmendis" in sh("sudo -n id 2>&1; id -un") and "uid=0" not in sh("sudo -n id 2>&1"))
    tc("TC-33", "Stage 6: flag not in environment", "IE3132" not in sh("env; cat /proc/1/environ 2>/dev/null"))
    c.close()

# ---- CTFd flag validation (optional) ----
if a.ctfd and a.token:
    H = {"Authorization": f"Token {a.token}", "Content-Type": "application/json"}
    chs = requests.get(a.ctfd + "/api/v1/challenges?view=admin", headers=H, verify=False).json()["data"]
    tc("TC-40", "CTFd has six challenges", len(chs) == 6, str(len(chs)))
    for ch, key in zip(sorted(chs, key=lambda c: c["name"]), ["cnr01", "cnr02", "cnr03", "cnr04", "cnr05", "cnr06"]):
        att = a.ctfd + "/api/v1/challenges/attempt"
        bad = requests.post(att, headers=H, verify=False, json={"challenge_id": ch["id"], "submission": "IE3132{wrong}"}).json()["data"]["status"]
        good = requests.post(att, headers=H, verify=False, json={"challenge_id": ch["id"], "submission": F[key]}).json()["data"]["status"]
        tc(f"TC-41-{key}", f"CTFd validates {ch['name']}", bad == "incorrect" and good in ("correct", "already_solved"), f"bad={bad} good={good}")

# ---- report ----
(ROOT / "tests/logs").mkdir(exist_ok=True)
ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
rp = ROOT / f"tests/logs/test_report_{ts}.md"
rows = "\n".join(f"| {i} | {d} | {r} | {x[:80]} |" for i, d, r, x in results)
rp.write_text("# CampusNet Rescue test report\n\n| ID | Test | Result | Detail |\n|---|---|---|---|\n" + rows + "\n")
fails = [r for r in results if r[2] == "FAIL"]
print(f"\n{len(results) - len(fails)}/{len(results)} passed -> {rp}")
sys.exit(1 if fails else 0)
