#!/usr/bin/env python3
"""Member 3 solver for CNR-06: parse the PCAP (scapy), find the flow from the Stage-5 attacker IP to an
unusual port, recover the credential rule from the plaintext HTTP note, then SSH in (paramiko) and read the
group-restricted file found with find/stat.
Usage: python3 solvers/m3_solve_stage6.py <pcap> <lab_host> <lab_code> <portal_id> <account> [port]"""
import sys, re, urllib.parse, collections, paramiko
from scapy.all import rdpcap, TCP, IP, Raw
pcap, host, labcode, portal, user = sys.argv[1:6]; port = int(sys.argv[6]) if len(sys.argv) > 6 else 2222
ATTACKER = "10.50.0.77"       # recovered from Stage 5 auth.log
pk = rdpcap(pcap)
syn = [p for p in pk if p.haslayer(TCP) and p[IP].src == ATTACKER and p[TCP].flags == 2]
print("attacker flows:", sorted({(p[IP].dst, p[TCP].dport) for p in syn}))
known = {80, 443, 8081}
odd = [p for p in syn if p[TCP].dport not in known]; print("unusual service port:", odd[0][TCP].dport, "on", odd[0][IP].dst)
text = b"".join(bytes(p[Raw].load) for p in pk if p.haslayer(Raw) and p[IP].src == ATTACKER and p[TCP].dport == 80).decode(errors="ignore")
body = urllib.parse.unquote_plus(text.split("\r\n\r\n", 1)[1]); print("note:", body)
password = f"{labcode}_{portal.lower()}"           # rule from the note: labcode_portalid-lowercase
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(host, port=port, username=user, password=password, look_for_keys=False, allow_agent=False, timeout=10)
def run(cmd): _, o, e = c.exec_command(cmd); return o.read().decode().strip()
print("$ id ->", run("id")); print("$ find / -group labaudit ->", run("find / -group labaudit -type f 2>/dev/null"))
path = [l for l in run("find / -group labaudit -type f 2>/dev/null").splitlines() if "incident_final" in l][0]
print("$ stat ->", run(f"stat -c '%A %U:%G %n' {path}")); print("FLAG:", run(f"cat {path}"))
c.close()
