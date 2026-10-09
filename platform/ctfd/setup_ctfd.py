#!/usr/bin/env python3
"""Member 1 - CTFd bootstrap. Runs the setup wizard (if needed), creates an API token, then imports
the six challenges (points, flags, hints with penalties, dependency chain, downloadable files).
Idempotent: existing challenges (by name) are skipped.
Env: CTFD_ADMIN_USER / CTFD_ADMIN_EMAIL / CTFD_ADMIN_PASSWORD, LAB_BIND_IP, optional CTFD_TOKEN (skip login)."""
import argparse, json, os, pathlib, re, sys, requests, urllib3

ROOT = pathlib.Path(__file__).resolve().parents[2]
FLAGS = json.load(open(ROOT / "author" / "flags.json"))
LAB = os.environ.get("LAB_BIND_IP", "127.0.0.1")

CHALLENGES = [
 dict(key="cnr01", name="CNR-01 Suspicious Student Profile", category="OSINT", value=100, files="cnr-01",
  desc="Lakeview Metropolitan University (fictional) lost confidential research material. A public project page, a directory and some profile fragments were recovered.\n\n"
       "Identify the campus identity connected to the leaked project, then find the **research lab code** that identity's own document carries.\n\n"
       "Flag format: `IE3132{LAB-CODE}` (use the code exactly as written).\n\n*Only the supplied files are in scope. Do not search for real people.*",
  hints=[("Compare repeated usernames and project references.", 10), ("The answer requires the directory plus one supplied profile page.", 20)]),
 dict(key="cnr02", name="CNR-02 Image in the Campus News", category="Steganography", value=150, files="cnr-02",
  desc="A promotional image from the project archive looks ordinary. Verify it, inspect it and recover what it hides.\n\nSubmit the archive tag from the recovered note as `IE3132{tag}`. Keep the rest of the note: you will need it.",
  hints=[("Begin with metadata and printable strings.", 10), ("The Stage 1 research lab code is relevant to the extraction step.", 20)]),
 dict(key="cnr03", name="CNR-03 Encoded Wi-Fi Notice", category="Cryptography", value=200, files="cnr-03",
  desc="An intercepted notice uses layered encoding and a weak classical cipher (intentionally weak - never use it for real data).\n\n"
       "Recover the plaintext. Submit `IE3132{portalid_token}` using lowercase for the portal id and the token exactly as written (case included), joined by an underscore.",
  hints=[("Identify the outer representation before considering a cipher.", 10), ("After the first decode, use the Stage 2 phrase as a key.", 20)]),
 dict(key="cnr04", name="CNR-04 Forgotten Student Portal", category="Web Security", value=250, files=None,
  desc=f"A forgotten training portal is still online (isolated lab service): `http://{LAB}:8081`. Use what Stage 3 revealed.\n\n"
       "Compare what the browser enforces with what the server actually checks, reach the restricted staff records page and submit its flag. Note the audit window - you will need it.\n\n"
       "*Only this lab address is in scope. Automated destructive scanning is not part of the intended path.*",
  hints=[("Compare what the browser disables with what the server actually checks.", 12), ("Capture the request that submits the records form and inspect its parameters.", 25)]),
 dict(key="cnr05", name="CNR-05 Lab Computer Footprints", category="Digital Forensics", value=300, files="cnr-05",
  desc="A workstation evidence package (synthetic) was preserved. Verify integrity, build a UTC timeline for the audit window from Stage 4 and identify the suspicious account, the artefact it produced and the time the suspicious session began.\n\nThe flag format is described in the evidence README. Work on copies only.",
  hints=[("Focus on the incident window revealed in Stage 4.", 15), ("Correlate authentication events with browser and filesystem activity.", 30)]),
 dict(key="cnr06", name="CNR-06 Final Campus Connection", category="Networking / Linux", value=400, files="cnr-06",
  desc=f"A focused packet capture and an isolated Linux service are available. The lab host maps the service to `{LAB}:2222` (the capture refers to it by its in-story address).\n\n"
       "Find the incident flows, identify the service, use ONLY information you recovered in earlier stages to reach it, and locate the final evidence. Scanning is allowed only against the lab address given above.",
  hints=[("Filter the capture using the Stage 5 event time and the Stage 5 source address.", 20), ("The unusual destination port identifies the service you should examine in the isolated lab.", 40)]),
]

class API:
    def __init__(s, base, verify):
        s.base, s.v, s.h = base.rstrip("/"), verify, {}
        s.sess = requests.Session()
    def req(s, m, path, **kw):
        r = s.sess.request(m, s.base + path, headers={**s.h, **kw.pop("headers", {})}, verify=s.v, **kw)
        return r

def nonce(html): 
    m = re.search(r'name="nonce"[^>]*value="([0-9a-f]+)"', html) or re.search(r'value="([0-9a-f]{64})"[^>]*name="nonce"', html)
    return m.group(1) if m else None

def bootstrap(api):
    admin_user = os.environ.get("CTFD_ADMIN_USER", "admin")
    admin_email = os.environ.get("CTFD_ADMIN_EMAIL", "admin@lakeview.invalid")
    admin_pw = os.environ["CTFD_ADMIN_PASSWORD"]
    r = api.req("GET", "/setup", allow_redirects=False)
    if r.status_code == 200:          # first run -> setup wizard
        print("Running CTFd setup wizard")
        data = dict(ctf_name="CampusNet Rescue", ctf_description="Investigate the Lakeview Metropolitan University incident (fictional).",
                    user_mode="users", challenge_visibility="private", account_visibility="private", score_visibility="private",
                    registration_visibility="private", verify_emails="false", team_size="", name=admin_user, email=admin_email,
                    password=admin_pw, ctf_theme="core", theme_color="", start="", end="", nonce=nonce(r.text))
        r = api.req("POST", "/setup", data=data, allow_redirects=True)
        if r.status_code >= 400: sys.exit(f"setup failed: {r.status_code}")
    # login
    r = api.req("GET", "/login"); n = nonce(r.text)
    r = api.req("POST", "/login", data={"name": admin_user, "password": admin_pw, "nonce": n}, allow_redirects=True)
    r = api.req("GET", "/admin/config")
    m = re.search(r"csrfNonce['\"]?\s*[:=]\s*['\"]([0-9a-f]+)['\"]", r.text)
    if not m: sys.exit("login/CSRF discovery failed - run the wizard manually and pass CTFD_TOKEN")
    t = api.req("POST", "/api/v1/tokens", json={"expiration": "2027-12-31", "description": "playbox-setup"}, headers={"CSRF-Token": m.group(1)})
    tok = t.json()["data"]["value"]
    return tok

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--base", default="https://127.0.0.1"); ap.add_argument("--insecure", action="store_true")
    a = ap.parse_args()
    if a.insecure: urllib3.disable_warnings()
    api = API(a.base, not a.insecure)
    tok = os.environ.get("CTFD_TOKEN") or bootstrap(api)
    api.h = {"Authorization": f"Token {tok}", "Content-Type": "application/json"}
    existing = {c["name"]: c["id"] for c in api.req("GET", "/api/v1/challenges?view=admin").json().get("data", [])}
    prev = None
    for c in CHALLENGES:
        if c["name"] in existing:
            cid = existing[c["name"]]; print("exists:", c["name"])
        else:
            r = api.req("POST", "/api/v1/challenges", json=dict(name=c["name"], category=c["category"], description=c["desc"],
                        value=c["value"], state="visible", type="standard"))
            cid = r.json()["data"]["id"]
            api.req("POST", "/api/v1/flags", json=dict(challenge_id=cid, content=FLAGS[c["key"]], type="static", data=""))
            for text, cost in c["hints"]:
                api.req("POST", "/api/v1/hints", json=dict(challenge_id=cid, content=text, cost=cost))
            if c["files"]:
                for f in sorted((ROOT / "dist" / c["files"]).iterdir()):
                    if f.name.startswith("_"): continue
                    api.req("POST", "/api/v1/files", headers={"Content-Type": None}, data={"challenge_id": cid, "type": "challenge"},
                            files={"file": (f.name, open(f, "rb"))})
            print("created:", c["name"], cid)
        if prev:
            api.req("PATCH", f"/api/v1/challenges/{cid}", json={"requirements": {"prerequisites": [prev], "anonymize": False}})
        prev = cid
    # registration open for participants once challenges exist
    api.req("PATCH", "/api/v1/configs", json={"registration_visibility": "public", "challenge_visibility": "private"})
    print("CTFd configured. Token (keep private):", tok[:6] + "...")
    open(ROOT / ".ctfd_token", "w").write(tok)

if __name__ == "__main__":
    main()
