#!/usr/bin/env bash
# Member 1. One-command deployment on a clean Ubuntu 22.04/24.04 VM with Docker Engine + Compose v2.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo "Docker not installed (see README section 2)"; exit 1; }
set -a; . ./.env; set +a
./scripts/gen_secrets_and_cert.sh
./scripts/verify_manifest.sh || ./scripts/verify_manifest.sh --restore
docker compose build stage4 stage6
docker compose up -d
echo "Waiting for CTFd..."; for i in $(seq 1 60); do curl -skf -o /dev/null https://$LAB_BIND_IP/ && break; sleep 3; done

python3 platform/ctfd/setup_ctfd.py --base https://$LAB_BIND_IP --insecure
sudo ./scripts/isolation.sh apply || echo "WARN: host firewall rules not applied (need sudo/iptables)"
./scripts/health_check.sh
