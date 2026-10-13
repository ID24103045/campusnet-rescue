#!/usr/bin/env python3
"""CNR-03 builder (Member 2). Layers: plaintext -> Vigenere(key) -> hex -> Base64.
Player reverses: Base64 decode -> hex decode -> Vigenere decrypt with Stage 2 key phrase."""
import json, pathlib, base64

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "dist" / "cnr-03"; OUT.mkdir(parents=True, exist_ok=True)
P = json.load(open(ROOT / "author" / "flags.json"))["params"]

def vig(text, key, decrypt=False):
    out, i = [], 0
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            k = ord(key[i % len(key)].upper()) - 65
            k = -k if decrypt else k
            out.append(chr((ord(ch) - base + k) % 26 + base)); i += 1
        else:
            out.append(ch)
    return "".join(out)

PLAIN = (f"NOTICE TO ALL STAFF. THE LEGACY TRAINING PORTAL IS STILL ONLINE AT /legacy/lantern-gate ON PORT 8081. "
         f"PORTAL ID: {P['portal_id']}. TOKEN: {P['portal_token']}.")

def encode(plain, key):
    return base64.b64encode(vig(plain, key).encode().hex().encode()).decode()

if __name__ == "__main__":
    enc = encode(PLAIN, P["vigenere_key"])
    (OUT / "wifi_notice.txt").write_text(
        "From: it-helpdesk@lakeview.invalid (fictional)\nSubject: Wi-Fi notice (intercepted copy)\n\n" + enc + "\n")
    assert vig(bytes.fromhex(base64.b64decode(enc).decode()).decode(), P["vigenere_key"], True) == PLAIN
    print("CNR-03 built ->", OUT / "wifi_notice.txt")
