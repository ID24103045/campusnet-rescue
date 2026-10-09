#!/usr/bin/env python3
"""CNR-01 builder: generates the fictional OSINT sources into dist/cnr-01/.
Owner: Member 2 (Challenge Design A). All people/orgs are fictional.
Logic: directory.html + project_lantern.html identify the alias (two sources);
the lab code exists ONLY in the PDF metadata of the document authored by that alias.
"""
import json, pathlib
from reportlab.pdfgen import canvas

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "dist" / "cnr-01"
OUT.mkdir(parents=True, exist_ok=True)
P = json.load(open(ROOT / "author" / "flags.json"))["params"]

STAFF = [
    # alias, name, role, unit, location, project
    ("a.perera",   "Amal Perera",     "Intern",             "Faculty of Business",  "Colombo City Campus", "Project Lantern"),
    ("s.jayasena", "Sanduni Jayasena","Research Assistant", "Faculty of Computing", "Malabe Lab Wing",    "Project Lantern"),
    ("k.wijesuriya","Kasun Wijesuriya","Lecturer",          "Faculty of Computing", "Malabe Main Block",   "Project Harbor"),
    ("n.fonseka",  "Nadee Fonseka",   "Student Ambassador", "Faculty of Business",  "Colombo City Campus", "Campus Radio"),
    ("t.mendis",   "Thilina Mendis",  "Lab Technician",     "Faculty of Computing", "Malabe Lab Wing",     "Network Lab Ops"),
    ("d.rathnayake","Dilini Rathnayake","Librarian",        "Learning Resources",   "Main Library",        "Archive Digitisation"),
    ("p.silva",    "Pasan Silva",     "Student Ambassador", "Faculty of Computing", "Malabe Main Block",   "Campus Radio"),
    ("m.herath",   "Menaka Herath",   "Research Assistant", "Faculty of Engineering","Kandy Centre",       "Project Harbor"),
]

def directory():
    rows = "\n".join(
        f'<tr data-alias="{a}"><td>{n}</td><td>{a}</td><td>{r}</td><td>{u}</td><td>{l}</td><td>{p}</td></tr>'
        for a, n, r, u, l, p in STAFF)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>Lakeview Metropolitan University - Staff and Student Directory</title>
<style>body{{font-family:sans-serif;margin:2rem}}table{{border-collapse:collapse}}td,th{{border:1px solid #888;padding:6px 10px}}th{{background:#223;color:#fff}}</style></head>
<body><h1>Lakeview Metropolitan University</h1><h2>Public Directory (FICTIONAL - CTF exercise)</h2>
<table><tr><th>Name</th><th>Alias</th><th>Role</th><th>Unit</th><th>Location</th><th>Project</th></tr>
{rows}
</table><p>Directory last synchronised: 2026-03-02.</p></body></html>"""

PROJECT = """<!doctype html><html><head><meta charset="utf-8"><title>Project Lantern - Public Page</title></head>
<body><h1>Project Lantern</h1>
<p>Project Lantern is an applied research initiative hosted by the <b>Faculty of Computing</b>.
Day-to-day work is carried out in the <b>Malabe Lab Wing</b> by a <b>Research Assistant</b>.</p>
<p>Our early budget summary was shared as <i>lantern_budget.pdf</i> and a campus club leaflet as <i>club_leaflet.pdf</i>.
Please do not redistribute outside the university.</p>
<!-- web editor note: both PDFs were exported from the same shared drive; check the document properties of each before circulating -->
</body></html>"""

FRAGMENTS = """<!doctype html><html><head><meta charset="utf-8"><title>Profile fragments</title></head><body>
<h2>Profile fragments recovered from the shared drive</h2>
<ul>
<li>"Presented the lantern pilot results to the faculty board. Working from the lab wing until the Colombo move." - posted by <b>a.perera</b> (intern placement, short-term)</li>
<li>"Thanks to the malabe lab team, bench access was sorted in time for the lantern demo." - posted by <b>m.herath</b></li>
<li>"Radio night is on Friday, bring snacks." - posted by <b>p.silva</b></li>
</ul></body></html>"""

def pdf(path, title, author, body, keywords):
    c = canvas.Canvas(str(path))
    c.setTitle(title); c.setAuthor(author); c.setSubject("Internal circulation (fictional)"); c.setKeywords(keywords)
    c.setFont("Helvetica-Bold", 16); c.drawString(72, 760, title)
    c.setFont("Helvetica", 11)
    y = 730
    for line in body:
        c.drawString(72, y, line); y -= 18
    c.save()

(OUT / "directory.html").write_text(directory())
(OUT / "project_lantern.html").write_text(PROJECT)
(OUT / "profile_fragments.html").write_text(FRAGMENTS)
pdf(OUT / "lantern_budget.pdf", "Project Lantern - Budget Summary", "s.jayasena",
    ["Budget summary (FICTIONAL).", "Equipment: 4 x lab switches, 2 x workstations.", "Status: draft v3. Approved by faculty board."],
    f"lab={P['lab_code']}; draft")
pdf(OUT / "club_leaflet.pdf", "Campus Club Leaflet", "a.perera",
    ["Colombo City Campus - Business Society leaflet (FICTIONAL).", "Join us on Friday for the open evening."],
    "lab=BZ-1032; leaflet")
print("CNR-01 built ->", OUT)
