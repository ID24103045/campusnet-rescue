#!/usr/bin/env bash
# Member 1. Health checks used after deploy/reset and by tests.
cd "$(dirname "$0")/.."
BIND=$(grep -E '^LAB_BIND_IP=' .env 2>/dev/null | cut -d= -f2); BIND=${BIND:-127.0.0.1}
ok=0
chk(){ if eval "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; ok=1; fi; }
chk "CTFd via nginx (443)"      "curl -sk https://$BIND/ -o /dev/null -w '%{http_code}' | grep -qE '200|302'"
chk "Stage 4 portal /healthz"   "curl -s http://$BIND:8081/healthz | grep -q ok"
chk "Stage 6 sshd banner (2222)" "timeout 5 bash -c 'exec 3<>/dev/tcp/$BIND/2222; head -c 8 <&3 | grep -q SSH-2.0'"
chk "Artefact manifest"         "./scripts/verify_manifest.sh"
chk "DB not published to host"  "! sudo ss -tln | grep -qE ':(3306|6379)\b'"
exit $ok
