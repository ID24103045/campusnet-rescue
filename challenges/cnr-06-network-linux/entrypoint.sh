#!/bin/sh
# Runs as root inside the container with capabilities dropped (see docker-compose.yml).
set -eu
ARCH=/srv/campus-archive/exports
mkdir -p "$ARCH"
cat > "$ARCH/export_index.csv" <<'EOT'
file,description
export_index.csv,this index
.incident_draft.txt,superseded draft (admin only)
.incident_final.txt,final incident record (labaudit)
EOT
echo "Draft notes - administrators only." > "$ARCH/.incident_draft.txt"
cp /run/secrets/stage6_flag "$ARCH/.incident_final.txt"
chown root:labaudit /srv/campus-archive "$ARCH" "$ARCH/export_index.csv" "$ARCH/.incident_final.txt"
chown root:root "$ARCH/.incident_draft.txt"
chmod 750 /srv/campus-archive "$ARCH"
chmod 644 "$ARCH/export_index.csv"
chmod 640 "$ARCH/.incident_final.txt"
chmod 600 "$ARCH/.incident_draft.txt"
mkdir -p /run
exec /usr/sbin/sshd -D -e -f /etc/ssh/sshd_config
