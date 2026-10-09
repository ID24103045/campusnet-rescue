#!/usr/bin/env python3
"""CNR-06 PCAP builder (Member 3). Synthetic capture: noise + decoys + the incident flows.
Incident (attacker 10.50.0.77): portal HTTP (:8081) -> internal wiki note (:80) -> SSH banner exchange (:2222)."""
import json, pathlib, random, hashlib
from scapy.all import Ether, IP, TCP, UDP, DNS, DNSQR, DNSRR, Raw, wrpcap

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "dist" / "cnr-06"; OUT.mkdir(parents=True, exist_ok=True)
P = json.load(open(ROOT / "author" / "flags.json"))["params"]
random.seed(2222)
import datetime as dt
T0 = dt.datetime(2026, 3, 14, 9, 30, 0, tzinfo=dt.timezone.utc).timestamp()
pkts = []
MAC = lambda ip: "02:00:00:00:%02x:%02x" % tuple(int(x) for x in ip.split(".")[2:])

def emit(p, t):
    p.time = t; pkts.append(p)

def tcp_session(c, s, sport, dport, t, exchanges, step=0.02):
    """exchanges: list of ('c'|'s', bytes). Builds handshake, data+acks, FIN."""
    cseq, sseq = random.randint(1000, 2**31), random.randint(1000, 2**31)
    def mk(src, dst, sp, dp, flags, seq, ack, data=b""):
        pk = Ether(src=MAC(src), dst=MAC(dst)) / IP(src=src, dst=dst) / TCP(sport=sp, dport=dp, flags=flags, seq=seq, ack=ack)
        return pk / Raw(data) if data else pk
    emit(mk(c, s, sport, dport, "S", cseq, 0), t); t += step; cseq += 1
    emit(mk(s, c, dport, sport, "SA", sseq, cseq), t); t += step; sseq += 1
    emit(mk(c, s, sport, dport, "A", cseq, sseq), t); t += step
    for who, data in exchanges:
        if who == "c":
            emit(mk(c, s, sport, dport, "PA", cseq, sseq, data), t); cseq += len(data); t += step
            emit(mk(s, c, dport, sport, "A", sseq, cseq), t)
        else:
            emit(mk(s, c, dport, sport, "PA", sseq, cseq, data), t); sseq += len(data); t += step
            emit(mk(c, s, sport, dport, "A", cseq, sseq), t)
        t += step
    emit(mk(c, s, sport, dport, "FA", cseq, sseq), t); t += step
    emit(mk(s, c, dport, sport, "FA", sseq, cseq + 1), t); t += step
    emit(mk(c, s, sport, dport, "A", cseq + 1, sseq + 1), t)

def http(host, method, path, body=b"", ctype="application/x-www-form-urlencoded", status="200 OK", resp=b"<html>ok</html>"):
    hdr = f"{method} {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: Mozilla/5.0\r\n"
    if body: hdr += f"Content-Type: {ctype}\r\nContent-Length: {len(body)}\r\n"
    req = hdr.encode() + b"\r\n" + body
    rsp = f"HTTP/1.1 {status}\r\nContent-Type: text/html\r\nContent-Length: {len(resp)}\r\n\r\n".encode() + resp
    return [("c", req), ("s", rsp)]

hosts = ["10.50.0.12", "10.50.0.15", "10.50.0.18", "10.50.0.21"]
# ---- background noise (DNS, NTP, web, HTTPS-like) over 40 minutes ----
for i in range(110):
    t = T0 + random.uniform(0, 2400); h = random.choice(hosts)
    kind = random.choice(["dns", "dns", "ntp", "web", "tls"])
    if kind == "dns":
        name = random.choice(["learn.lakeview.invalid", "mail.lakeview.invalid", "news.lakeview.invalid"])
        q = Ether(src=MAC(h), dst=MAC("10.50.0.1")) / IP(src=h, dst="10.50.0.1") / UDP(sport=random.randint(30000, 60000), dport=53) / DNS(rd=1, qd=DNSQR(qname=name))
        emit(q, t)
        r = Ether(src=MAC("10.50.0.1"), dst=MAC(h)) / IP(src="10.50.0.1", dst=h) / UDP(sport=53, dport=q[UDP].sport) / DNS(id=q[DNS].id, qr=1, qd=q[DNS].qd, an=DNSRR(rrname=name, rdata="10.50.0.60"))
        emit(r, t + 0.01)
    elif kind == "ntp":
        emit(Ether(src=MAC(h), dst=MAC("10.50.0.1")) / IP(src=h, dst="10.50.0.1") / UDP(sport=123, dport=123) / Raw(b"\x23" + b"\x00" * 47), t)
    elif kind == "web":
        tcp_session(h, "10.50.0.60", random.randint(30000, 60000), 80, t, http("learn.lakeview.invalid", "GET", "/modules"))
    else:
        tcp_session(h, "10.50.0.60", random.randint(30000, 60000), 443, t, [("c", b"\x16\x03\x01" + bytes(random.getrandbits(8) for _ in range(120))), ("s", b"\x16\x03\x03" + bytes(random.getrandbits(8) for _ in range(300)))])
# ---- decoys: unusual-but-benign ports from normal hosts ----
tcp_session("10.50.0.15", "10.50.0.40", 50777, 9090, T0 + 900, http("monitor.lakeview.invalid:9090", "GET", "/metrics", resp=b"# HELP up\nup 1\n"))
tcp_session("10.50.0.18", "10.50.0.41", 50888, 8443, T0 + 1500, [("c", b"\x16\x03\x01" + b"A" * 90), ("s", b"\x16\x03\x03" + b"B" * 200)])
# ---- incident flows (09:53 - 09:58 UTC) ----
A = "10.50.0.77"
t1 = dt.datetime(2026, 3, 14, 9, 53, 40, tzinfo=dt.timezone.utc).timestamp()
tcp_session(A, "10.50.0.30", 51600, 8081, t1, http("10.50.0.30:8081", "GET", "/legacy/lantern-gate", resp=b"<html>portal</html>"))
tcp_session(A, "10.50.0.30", 51602, 8081, t1 + 30, http("10.50.0.30:8081", "POST", "/legacy/lantern-gate/request",
            body=b"student_id=S0001&module=NET101&access_level=staff", status="302 FOUND", resp=b""))
note = ("title=scratch&body=maintenance+shell+is+on+tcp%2F2222+of+the+new+archive+box+10.50.0.31.+"
        "login+is+the+account+we+got+earlier.+password+rule%3A+labcode_portalid-lowercase.+"
        "the+export+folder+is+handled+by+group+labaudit.").encode()
tcp_session(A, "10.50.0.50", 51610, 80, t1 + 170, http("wiki.lakeview.invalid", "POST", "/wiki/pages/scratch", body=note, status="201 CREATED", resp=b"saved"))
kex = bytes(random.getrandbits(8) for _ in range(600))
tcp_session(A, "10.50.0.31", 51622, 2222, t1 + 263,
            [("s", b"SSH-2.0-OpenSSH_9.7\r\n"), ("c", b"SSH-2.0-OpenSSH_9.6p1 Ubuntu-3\r\n"), ("c", kex[:300]), ("s", kex[300:]), ("c", kex[:120]), ("s", kex[120:240])])
pkts.sort(key=lambda p: p.time)
out = OUT / "campus_capture.pcap"
wrpcap(str(out), pkts)
print("CNR-06 pcap ->", out, len(pkts), "packets", hashlib.sha256(out.read_bytes()).hexdigest()[:16])
