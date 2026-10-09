#!/usr/bin/env bash
# Rebuilds every file-based artefact deterministically into dist/ and refreshes the SHA-256 manifest.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 challenges/cnr-01-osint/build.py
python3 challenges/cnr-02-stego/build.py      # needs steghide
python3 challenges/cnr-03-crypto/build.py
python3 challenges/cnr-05-forensics/build.py
python3 challenges/cnr-06-network-linux/build_pcap.py
find dist -type f | sort | xargs sha256sum > manifests/SHA256SUMS
chmod -R u+w master 2>/dev/null || true; rm -rf master && mkdir master && cp -r dist/. master/ && chmod -R a-w master   # read-only master copy for reset
echo "artefacts + manifest + read-only master ready"
