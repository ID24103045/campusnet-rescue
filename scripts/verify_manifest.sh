#!/usr/bin/env bash
# Verifies dist/ against manifests/SHA256SUMS; with --restore, re-copies tampered files from the read-only master.
set -uo pipefail
cd "$(dirname "$0")/.."
if sha256sum --quiet -c manifests/SHA256SUMS 2>/dev/null; then echo "MANIFEST OK"; exit 0; fi
echo "MANIFEST MISMATCH"
if [ "${1:-}" = "--restore" ]; then
  [ -d master ] || { echo "no master copy"; exit 2; }
  chmod -R u+w dist; rm -rf dist; mkdir dist; cp -r master/. dist/; chmod -R u+w dist
  sha256sum --quiet -c manifests/SHA256SUMS && echo "RESTORED OK" && exit 0
fi
exit 1
