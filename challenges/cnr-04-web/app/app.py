"""CNR-04 Forgotten Student Portal - INTENTIONALLY VULNERABLE (CTF only). Owner: Member 3.
Weakness: the 'access_level' choice is restricted only in the browser (disabled <select> + JS).
The server trusts the posted value. Everything else is validated normally."""
import os, sqlite3, secrets, logging, json, time
from flask import Flask, request, session, redirect, render_template_string, abort, make_response

BASE = "/legacy/lantern-gate"
PORTAL_ID = os.environ.get("PORTAL_ID", "LANTERNGATE").upper()
FLAG_FILE = os.environ.get("FLAG_FILE", "/run/secrets/stage4_flag")
DB = os.environ.get("DB_PATH", "/data/portal.db")

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)          # new key each start -> old cookies invalid after reset
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("portal")

def init_db():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("DROP TABLE IF EXISTS requests")
    con.execute("CREATE TABLE requests (id INTEGER PRIMARY KEY, student_id TEXT, module TEXT, level TEXT, ts REAL)")
    con.commit(); con.close()

def read_flag():
    try:
        return open(FLAG_FILE).read().strip()
    except OSError:
        return "FLAG-NOT-CONFIGURED"

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Lakeview Training Portal (legacy)</title>
<style>body{font-family:sans-serif;max-width:640px;margin:2rem auto}input,select,button{padding:6px;margin:4px 0}.box{border:1px solid #888;padding:1rem}</style></head>
<body><h1>Lakeview Training Portal <small>(legacy)</small></h1>{{ body|safe }}</body></html>"""

def page(body, code=200):
    r = make_response(render_template_string(PAGE, body=body), code); return r

@app.after_request
def _log(resp):
    log.info("%s %s %s -> %s", request.remote_addr, request.method, request.full_path.rstrip("?"), resp.status_code)
    return resp

@app.route("/")
def root():
    return redirect(BASE)

@app.route(BASE, methods=["GET", "POST"])
def gate():
    msg = ""
    if request.method == "POST":
        if request.form.get("portal_id", "").strip().upper() == PORTAL_ID:
            session["gate"] = True
            return redirect(BASE + "/request")
        msg = "<p style='color:#b00'>Unknown portal identifier.</p>"
    return page(f"""<div class="box"><p>Enter the portal identifier shown on your training notice.</p>{msg}
<form method="post"><input name="portal_id" placeholder="Portal ID"><button>Enter</button></form></div>""")

@app.route(BASE + "/request", methods=["GET", "POST"])
def access_request():
    if not session.get("gate"):
        return redirect(BASE)
    if request.method == "POST":
        sid = request.form.get("student_id", "")[:20]
        module = request.form.get("module", "")[:30]
        level = request.form.get("access_level", "student")   # <-- trusted from client (the flaw)
        if not sid.isalnum() or module not in ("NET101", "SEC201", "OPS110"):
            return page("<p style='color:#b00'>Invalid student ID or module.</p><a href='%s/request'>Back</a>" % BASE, 400)
        if level not in ("student", "staff"):
            return page("<p style='color:#b00'>Unknown access level.</p><a href='%s/request'>Back</a>" % BASE, 400)
        con = sqlite3.connect(DB)
        con.execute("INSERT INTO requests (student_id, module, level, ts) VALUES (?,?,?,?)", (sid, module, level, time.time()))
        con.commit(); con.close()
        if level == "staff":
            session["staff_grant"] = True
            return redirect(BASE + "/records/restricted")
        return page(f"<div class='box'><p>Request recorded for <b>{sid}</b> / {module} at <b>student</b> level.</p>"
                    f"<p>Staff-level records are not available to students.</p></div>")
    return page(f"""<div class="box"><h3>Training records request</h3>
<form method="post" id="f">
<label>Student ID <input name="student_id" required></label><br>
<label>Module <select name="module"><option>NET101</option><option>SEC201</option><option>OPS110</option></select></label><br>
<label>Access level <select name="access_level" id="lvl" disabled>
<option value="student" selected>student</option><option value="staff">staff (locked)</option></select></label><br>
<input type="hidden" name="access_level" value="student">
<button>Submit request</button></form>
<script>/* UI rule: students may not choose staff level */ document.getElementById('lvl').value='student';</script></div>""")

@app.route(BASE + "/records/restricted")
def restricted():
    if not session.get("staff_grant"):
        abort(403)
    return page(f"""<div class="box"><h3>Restricted staff records (training copy)</h3>
<p>Audit note: abnormal portal activity was logged between <b>2026-03-14 09:30 and 10:15 UTC</b>.</p>
<p>Challenge flag: <code>{read_flag()}</code></p></div>""")

@app.route("/healthz")
def health():
    return {"status": "ok"}

init_db()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
