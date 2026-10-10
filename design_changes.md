# Changes from the Assignment 01 design (Member 4 segment)

| # | Assignment 01 | As built | Technical justification |
|---|---|---|---|
| 1 | Stage 6 container "runs unprivileged" | Starts as root inside the container but with `cap_drop: ALL`, only CHOWN/FOWNER/SETUID/SETGID/SYS_CHROOT added, `no-new-privileges`, read-only rootfs, tmpfs state, no sudo | sshd must start as root to change to the logged-in user (privilege separation). Running it fully non-root would only allow logging in as that same user, breaking the group-permission puzzle. |
| 2 | Challenge network `internal` Docker network | Normal bridge with `enable_ip_masquerade=false` plus host DOCKER-USER rules (`scripts/isolation.sh`) | Docker does not publish ports for containers attached only to internal networks, so participants could not reach stages 4 and 6. No NAT + explicit DROP rules give the same "no egress" result and are testable (`isolation_test.sh`). |
| 3 | Ports "8081 or mapped" / "2222 or assigned" | Fixed 8081 (portal) and 2222 (SSH), bound to `LAB_BIND_IP` | Predictable for the PCAP and the platform text. |
| 4 | Stage 4 DB "SQLite seed data on named volume" | SQLite on tmpfs, recreated at container start | Reset becomes simply recreating the container; no persistent state to forget. |
| 5 | Stage 4 hint 2 mentioned the Stage 3 identifier | Hint 2 points to capturing the records-form request | The Stage 3 identifier is used on the entry page; the weakness is in the form request. |
| 6 | Stage 3 flag value unspecified | `IE3132{portalid-lowercase_TOKEN}` token case preserved | Removes ambiguity (risk R6). |
| 7 | Stage 5 flag format unspecified | `IE3132{account_artefact_YYYYMMDDTHHMMSSZ}`; artefact lowercased with `.`/`_` -> `-`; time = accepted login in UTC (rule printed in the evidence README) | Deterministic answer, single interpretation. |
| 8 | Stage 6 "challenge credential fragments" | SSH user = Stage 5 account; password rule (`labcode_portalid-lowercase`) is found as a plaintext HTTP note inside the PCAP | Makes the PCAP necessary, not just the port scan, and keeps credentials out of image layers/env. |
| 9 | Tool "steerhide" | `steghide` on a JPEG | Spelling error in the proposal; steghide is the intended tool. |
| 10 | Stage 6 hint 1 "use the Stage 5 event time" | Also mentions the Stage 5 source address | Without it the capture is very noisy for a 3rd-year audience. |
| 11 | Nginx/TLS optional | Included with a self-signed lab certificate | Matches the architecture figure (HTTPS 443). |
