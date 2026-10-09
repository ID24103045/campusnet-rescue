#!/usr/bin/env python3
"""Member 2 solver for CNR-01..03 (information gathering -> extraction -> decoding).
Usage: python3 solvers/m2_solve_stage1_3.py [dist_dir]
Needs: steghide, pypdf.  Prints each stage's flag and the clue it hands to the next stage."""
import re, sys, base64, pathlib, subprocess, tempfile
from html.parser import HTMLParser
from pypdf import PdfReader

D = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[1] / "dist")

class Rows(HTMLParser):
    def __init__(s): super().__init__(); s.rows, s.cur, s.cell = [], None, None
    def handle_starttag(s, t, a):
        if t == "tr": s.cur = []
        if t == "td": s.cell = ""
    def handle_data(s, d):
        if s.cell is not None: s.cell += d
    def handle_endtag(s, t):
        if t == "td": s.cur.append(s.cell); s.cell = None
        if t == "tr" and s.cur: s.rows.append(s.cur); s.cur = None

def stage1():
    """Source 1+2: project page names unit/location/role -> match against directory -> alias;
    Source 3: PDF whose Author == alias holds the lab code in its metadata."""
    page = (D / "cnr-01/project_lantern.html").read_text()
    unit = re.search(r"hosted by the <b>(.*?)</b>", page).group(1)
    loc = re.search(r"carried out in the <b>(.*?)</b>", page).group(1)
    role = re.search(r"by a <b>(.*?)</b>", page).group(1)
    p = Rows(); p.feed((D / "cnr-01/directory.html").read_text())
    match = [r for r in p.rows if r[2] == role and r[3] == unit and r[4] == loc and r[5] == "Project Lantern"]
    assert len(match) == 1, f"expected exactly one identity, got {match}"
    alias = match[0][1]
    for pdf in (D / "cnr-01").glob("*.pdf"):
        meta = PdfReader(str(pdf)).metadata
        if meta.author == alias:
            code = re.search(r"lab=([A-Z]+-\d+)", meta.get("/Keywords", "")).group(1)
            return alias, code
    raise SystemExit("no PDF authored by alias")

def stage2(lab_code):
    with tempfile.TemporaryDirectory() as t:
        out = pathlib.Path(t) / "note.txt"
        subprocess.run(["steghide", "extract", "-sf", str(D / "cnr-02/campus_news.jpg"), "-p", lab_code, "-xf", str(out), "-q"], check=True)
        note = out.read_text()
    return re.search(r"ARCHIVE-TAG: (\S+)", note).group(1), re.search(r"NEXT-KEY-PHRASE: (\S+)", note).group(1)

def vig_dec(text, key):
    o, i = [], 0
    for ch in text:
        if ch.isalpha():
            b = 65 if ch.isupper() else 97
            o.append(chr((ord(ch) - b - (ord(key[i % len(key)].upper()) - 65)) % 26 + b)); i += 1
        else: o.append(ch)
    return "".join(o)

def stage3(key):
    blob = (D / "cnr-03/wifi_notice.txt").read_text().strip().splitlines()[-1]
    hexed = base64.b64decode(blob).decode()                  # layer 1: Base64
    cipher = bytes.fromhex(hexed).decode()                   # layer 2: hex
    plain = vig_dec(cipher, key)                             # layer 3: Vigenere (key from stage 2)
    pid = re.search(r"PORTAL ID: (\S+?)\.", plain).group(1); tok = re.search(r"TOKEN: (\S+?)\.", plain).group(1)
    return plain, pid, tok

if __name__ == "__main__":
    alias, code = stage1();             print(f"[1] alias={alias} lab_code={code}\n    FLAG: IE3132{{{code}}}")
    tag, key = stage2(code);            print(f"[2] tag={tag} key_phrase={key}\n    FLAG: IE3132{{{tag}}}")
    plain, pid, tok = stage3(key);      print(f"[3] plaintext={plain}\n    FLAG: IE3132{{{pid.lower()}_{tok}}}")
