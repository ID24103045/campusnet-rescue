#!/usr/bin/env bash
# Member 1/4. Proves the challenge containers are isolated. Run on the lab host after deploy.
cd "$(dirname "$0")/.."
rc=0
t(){ # desc, expect(blocked|allowed), command inside stage4 (python available)
  if docker compose exec -T stage4 python -c "$3" >/dev/null 2>&1; then r=allowed; else r=blocked; fi
  [ "$r" = "$2" ] && echo "PASS  $1 ($r)" || { echo "FAIL  $1 (got $r, expected $2)"; rc=1; }; }
CONN="import socket,sys;s=socket.socket();s.settimeout(3);s.connect(('%s',%s))"
t "stage4 -> internet 1.1.1.1:53"        blocked "$(printf "$CONN" 1.1.1.1 53)"
t "stage4 -> DNS name resolution"        blocked "import socket;socket.gethostbyname('example.com')"
t "stage4 -> control net DB 10.40.0.1:3306" blocked "$(printf "$CONN" 10.40.0.1 3306)"
t "stage4 -> host gateway 10.50.0.1:22"  blocked "$(printf "$CONN" 10.50.0.1 22)"
t "stage4 -> stage6 peer 10.50.0.31:2222" allowed "$(printf "$CONN" 10.50.0.31 2222)"
echo "--- container hardening ---"
for s in stage4 stage6; do
  id=$(docker compose ps -q $s)
  echo "$s: user/caps/readonly/mounts"
  docker inspect "$id" --format '  User={{.Config.User}} ReadonlyRootfs={{.HostConfig.ReadonlyRootfs}} CapDrop={{.HostConfig.CapDrop}} Privileged={{.HostConfig.Privileged}} NoNewPriv={{.HostConfig.SecurityOpt}}'
  docker inspect "$id" --format '  Mounts: {{range .Mounts}}{{.Type}}:{{.Destination}} {{end}}'
  docker inspect "$id" --format '{{range .Mounts}}{{.Source}}{{"\n"}}{{end}}' | grep -q docker.sock && { echo "FAIL docker.sock mounted"; rc=1; } || echo "  PASS no docker.sock"
done
exit $rc
