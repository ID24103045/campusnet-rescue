#!/usr/bin/env bash
# Member 1. Reset / recovery. Usage: reset.sh {files|stage4|stage6|challenges|ctfd|all}
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
case "${1:-}" in
  files)  ./scripts/verify_manifest.sh --restore ;;
  stage4) docker compose up -d --force-recreate --no-deps stage4 ;;           # DB lives on tmpfs => state wiped
  stage6) docker compose up -d --force-recreate --no-deps stage6 ;;           # flag rewritten from secret, perms reset
  challenges) "$0" stage4; "$0" stage6; "$0" files ;;
  ctfd)   # wipe scoreboard + re-import challenges (CTFd volumes ONLY, named explicitly)
          docker compose stop ctfd db cache nginx
          docker compose rm -f ctfd db cache nginx
          docker volume rm campusnet-rescue_db_data campusnet-rescue_ctfd_uploads || true
          docker compose up -d nginx ctfd db cache
          for i in $(seq 1 60); do curl -skf -o /dev/null https://$LAB_BIND_IP/ && break; sleep 3; done
          set -a; . ./.env; set +a
          python3 platform/ctfd/setup_ctfd.py --base https://$LAB_BIND_IP --insecure ;;
  all)    "$0" challenges; "$0" ctfd ;;
  *) echo "usage: $0 {files|stage4|stage6|challenges|ctfd|all}"; exit 1 ;;
esac
sleep 6
./scripts/health_check.sh || true
