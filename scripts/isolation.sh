#!/usr/bin/env bash
# Member 1. Host firewall rules (DOCKER-USER chain) so challenge containers (10.50.0.0/24) cannot reach
# the host, the control network or anything outside. Usage: sudo isolation.sh {apply|remove|status}
set -euo pipefail
CH=10.50.0.0/24; CTRL=10.40.0.0/24
case "${1:-status}" in
 apply)
  iptables -N CTF-ISO 2>/dev/null || iptables -F CTF-ISO
  iptables -A CTF-ISO -s $CH -d $CH -j ACCEPT                          # peer traffic inside challenge net only
  iptables -A CTF-ISO -s $CH -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT   # replies to published ports
  iptables -A CTF-ISO -s $CH -d $CTRL -j DROP                          # challenge -> control net
  iptables -A CTF-ISO -s $CH -j DROP                                   # challenge -> anywhere else (internet, LAN)
  iptables -A CTF-ISO -d $CH -j RETURN
  iptables -C DOCKER-USER -j CTF-ISO 2>/dev/null || iptables -I DOCKER-USER 1 -j CTF-ISO
  iptables -C INPUT -s $CH -m conntrack --ctstate NEW -j DROP 2>/dev/null || iptables -I INPUT 1 -s $CH -m conntrack --ctstate NEW -j DROP   # challenge -> host itself (INPUT, not forwarded)
  echo "isolation applied";;
 remove) iptables -D DOCKER-USER -j CTF-ISO 2>/dev/null || true; iptables -D INPUT -s $CH -m conntrack --ctstate NEW -j DROP 2>/dev/null || true; iptables -F CTF-ISO 2>/dev/null || true; iptables -X CTF-ISO 2>/dev/null || true; echo removed;;
 status) iptables -S CTF-ISO 2>/dev/null || echo "not applied"; iptables -S INPUT | grep -- "$CH" || true;;
esac
