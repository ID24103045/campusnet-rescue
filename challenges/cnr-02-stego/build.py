#!/usr/bin/env python3
"""CNR-02 builder (Member 2). Creates campus_news.jpg with a steghide-embedded note.
Passphrase = Stage 1 lab code. Requires: pillow, steghide (apt install steghide)."""
import json, pathlib, subprocess, random, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "dist" / "cnr-02"; OUT.mkdir(parents=True, exist_ok=True)
cfg = json.load(open(ROOT / "author" / "flags.json")); P = cfg["params"]

random.seed(417)  # deterministic cover image
img = Image.new("RGB", (900, 500), (20, 40, 80))
d = ImageDraw.Draw(img)
for _ in range(260):  # simple procedural 'campus skyline' noise (steghide needs texture)
    x, y = random.randint(0, 880), random.randint(120, 480)
    w, h = random.randint(10, 60), random.randint(20, 200)
    c = tuple(random.randint(40, 180) for _ in range(3))
    d.rectangle([x, y, x + w, y + h], fill=c)
d.rectangle([0, 0, 900, 110], fill=(10, 20, 50))
d.text((30, 40), "LAKEVIEW CAMPUS NEWS - Open Day Special (FICTIONAL)", fill=(255, 255, 255))
cover = OUT / "_cover.jpg"
img.save(cover, "JPEG", quality=92)

note = (
    "Lakeview press archive note (synthetic)\n"
    f"ARCHIVE-TAG: {P['stego_note_tag']}\n"
    f"NEXT-KEY-PHRASE: {P['vigenere_key']}\n"
    "Use the key phrase for the encoded Wi-Fi notice.\n"
)
with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
    f.write(note); notepath = f.name
final = OUT / "campus_news.jpg"
if final.exists(): final.unlink()
subprocess.run(["steghide", "embed", "-cf", str(cover), "-ef", notepath, "-sf", str(final),
                "-p", P["lab_code"], "-q"], check=True)
cover.unlink(); pathlib.Path(notepath).unlink()
# harmless metadata clue (does NOT contain key or flag)
subprocess.run(["exiftool", "-overwrite_original", "-Artist=Lakeview Press Office",
                "-Comment=Original archive copy. Payload tool: steghide-compatible. Passphrase is a lab identifier from the project documents.",
                str(final)], check=True, stdout=subprocess.DEVNULL)
print("CNR-02 built ->", final)
