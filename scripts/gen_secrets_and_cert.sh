#!/usr/bin/env bash
# Member 1. Writes Docker secrets from author/flags.json and a self-signed TLS cert for the lab.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p secrets platform/certs
python3 - <<'PY'
import json
f=json.load(open("author/flags.json"))
for k,n in (("cnr04","stage4_flag"),("cnr06","stage6_flag")):
    open(f"secrets/{n}.txt","w").write(f[k]+"\n")
PY
chmod 644 secrets/*.txt   # container users (10001 / root) must read them; dir stays host-private
if [ ! -f platform/certs/ctf.crt ]; then
  openssl req -x509 -nodes -newkey rsa:2048 -days 30 -subj "/CN=campusnet-rescue.lab" \
    -keyout platform/certs/ctf.key -out platform/certs/ctf.crt 2>/dev/null
fi
[ -f .env ] || { cp .env.example .env; echo "Created .env from template - edit secrets before real use."; }
echo "secrets + cert ready"
